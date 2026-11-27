import { createRequire } from 'node:module';

export const name = 'strata-skills';
export const inject = ['tools', 'skills', 'workingDirectory'];

// Use the same package instances as the running Harness, including a source-checkout Harness.
const harnessRequire = () => createRequire(process.argv[1]);

export function apply(ctx) {
  const require = harnessRequire();
  const { isModelInvocable, isSkillName, isUserInvocable, renderSkillContent } = require('@deepseek-ai/dsh-skill');
  const { createUserMessage } = require('@deepseek-ai/dsh-llm');
  const scopeFor = async (agent, signal) => ({
    cwd: agent ? await ctx.workingDirectory.ensure(agent, signal) : undefined,
    signal,
    scope: agent,
  });
  const response = {
    schema: { type: 'object', additionalProperties: true },
    render: (_args, value) => [{ type: 'text', text: value.content ?? JSON.stringify(value) }],
  };

  ctx.tools.register({
    name: 'skills_list',
    description: 'Find relevant saved workflow skills when a task may match one. Search by name or description, then call skill with an exact name to read the instructions.',
    parameters: { type: 'object', additionalProperties: false, properties: {
      query: { type: 'string', maxLength: 128, description: 'Keywords from the skill name or description. Omit to browse.' },
      offset: { type: 'integer', minimum: 0, description: 'Use the nextOffset from the previous page with the same query.' },
    } },
    output: response,
    async execute({ query = '', offset = 0 }, { agent, signal }) {
      const words = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
      const summaries = await ctx.skills.list(await scopeFor(agent, signal));
      const matches = summaries.filter(skill => {
        if (!isModelInvocable(skill)) return false;
        const metadata = `${skill.name} ${skill.description}`.toLowerCase();
        return words.every(word => metadata.includes(word));
      }).sort((a, b) => a.name.localeCompare(b.name));
      const limit = 12;
      return {
        skills: matches.slice(offset, offset + limit).map(({ name, description }) => ({
          name, description: description.replace(/\s+/g, ' ').trim().slice(0, 140),
        })),
        nextOffset: offset + limit < matches.length ? offset + limit : null,
      };
    },
    isConcurrencySafe: () => true,
  });
  ctx.tools.register({
    name: 'skill',
    description: 'Load the complete instructions for a named skill. Use skills_list to discover relevant skills if the name is unknown.',
    parameters: { type: 'object', additionalProperties: false, required: ['name'], properties: { name: { type: 'string', maxLength: 64 } } },
    output: response,
    async execute(args, { agent, signal }) {
      if (!isSkillName(args.name)) throw new Error('Invalid skill name.');
      const lookup = await scopeFor(agent, signal);
      const summary = (await ctx.skills.list(lookup)).find(skill => skill.name === args.name);
      const skill = summary && isModelInvocable(summary) ? await ctx.skills.get(args.name, lookup) : undefined;
      if (!skill || !isModelInvocable(skill)) throw new Error(`Skill ${args.name} is unavailable for model invocation.`);
      return { name: skill.name, provider: skill.provider, resourceBase: skill.resourceBase, content: renderSkillContent(skill) };
    },
    presentCall: args => ({ card: 'generic', title: `Load skill ${args.name}`, kind: 'read', rawInput: args.name }),
  });

  // Keep deliberate /skill-name invocations, including skills hidden from model discovery.
  ctx.on('agent/pre-step', async ({ agent, messages, signal }, next) => {
    const decision = await next();
    if (decision.kind === 'reject') return decision;
    const names = new Set();
    for (const message of messages) {
      if (message.source.kind !== 'user') continue;
      for (const block of message.content) {
        if (block.type !== 'text') continue;
        for (const [, skillName] of block.text.matchAll(/(?:^|\s)\/([a-z0-9]+(?:-[a-z0-9]+)*)(?=\s|$)/g)) names.add(skillName);
      }
    }
    if (!names.size) return decision;
    const lookup = await scopeFor(agent, signal);
    const injections = [];
    for (const skillName of names) {
      const skill = await ctx.skills.get(skillName, lookup);
      signal.throwIfAborted();
      if (!skill || !isUserInvocable(skill)) continue;
      injections.push(createUserMessage({
        content: [{ type: 'text', text: renderSkillContent(skill) }],
        source: { kind: 'skill-invocation', name: skillName, form: 'instructions' },
      }));
    }
    return injections.length ? { ...decision, messages: [...decision.messages, ...injections] } : decision;
  });
}

// Retire only old automatic lists from the active surface, keeping their original events on disk.
// Use the request hook, after the step opens, so the replacement is also valid on disk.
export function retireSkillCatalogues(ctx) {
  const { createSystemMessage } = harnessRequire()('@deepseek-ai/dsh-llm');
  ctx.on('agent/request', ({ agent, turn, step, signal }, next) => {
    signal.throwIfAborted();
    const session = agent.session;
    for (const seq of session.surface.nodes) {
      const event = session.eventAt(seq);
      if (event?.type !== 'user/message' || event.data.source.kind !== 'skill-catalog') continue;
      session.append('system/message', { turn, step, message: createSystemMessage('') }, {
        surfaceOp: { op: 'replace', startSeq: seq, endSeq: seq }, sourceEventSeqs: [seq],
      });
    }
    return next();
  });
}
