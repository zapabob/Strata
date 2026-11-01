/** Hikari / local GGUF must be eligible for the agent (web_search path). */
import test from 'node:test';
import assert from 'node:assert/strict';
import {
  supervisorIsReady,
  supervisorLocalInstance,
  mergeAgentLocalInstances,
  agentHasLocalModel,
  agentSkipReason,
} from '../server/agent-local.mjs';

test('supervisor ready gate rejects starting/stopped engines', () => {
  assert.equal(supervisorIsReady({ status: 'running', modelId: 'local-hikari', port: 8080 }), true);
  assert.equal(supervisorIsReady({ status: 'starting', modelId: 'local-hikari', port: 8080 }), false);
  assert.equal(supervisorIsReady({ status: 'running', modelId: null, port: 8080 }), false);
  assert.equal(supervisorIsReady({ status: 'running', modelId: 'x', port: 0 }), false);
});

test('supervisorLocalInstance builds an agent route for Hikari-style GGUF', () => {
  const row = supervisorLocalInstance(
    { status: 'running', modelId: 'local-e7d83e78598be18b75bf0498', port: 8080 },
    { authenticationKey: () => 'sk-test', label: 'Hikari', context: 131072 },
  );
  assert.equal(row.id, 'supervisor:local-e7d83e78598be18b75bf0498');
  assert.equal(row.baseUrl, 'http://127.0.0.1:8080/v1');
  assert.equal(row.modelId, 'local');
  assert.equal(row.key, 'sk-test');
  assert.equal(row.label, 'Hikari');
  assert.equal(row.source, 'supervisor');
  assert.equal(supervisorLocalInstance({ status: 'stopped', modelId: 'x', port: 8080 }), null);
});

test('merge prefers native ids and still adds supervisor Hikari', () => {
  const native = [{ id: 'n1', label: 'Native' }];
  const hikari = supervisorLocalInstance(
    { status: 'running', modelId: 'local-hikari', port: 8080 },
    { label: 'Hikari' },
  );
  const merged = mergeAgentLocalInstances(native, hikari);
  assert.deepEqual(merged.map(r => r.id), ['n1', 'supervisor:local-hikari']);
  assert.equal(mergeAgentLocalInstances(native, null).length, 1);
});

test('agent skip allows supervisor-only Hikari (web search can reach it)', () => {
  assert.equal(agentHasLocalModel({ supervisorLive: true }), true);
  assert.equal(agentSkipReason({
    chatId: 'c1', remoteModel: false, nativeLive: false, supervisorLive: true,
  }), null);
  assert.match(agentSkipReason({
    chatId: 'c1', remoteModel: false, nativeLive: false, supervisorLive: false,
  }), /local GGUF|API model|Strata model/);
  assert.match(agentSkipReason({ plainChat: true, chatId: 'c1', supervisorLive: true }), /without the agent/);
});
