import { useEffect, useId, useState } from 'react';
import { api } from '../lib/client';
import { userError } from '../lib/format';
import { tr } from '../lib/i18n';
import { Btn, Dialog, Icon, IconBtn } from '../components/ui';
import './WorkspaceFiles.css';

interface Entry { name: string; path: string; kind: 'file' | 'dir'; revision: string; sizeKb: number }
interface Listing { path: string; entries: Entry[]; nextOffset: number | null }
interface Document { path: string; text: string; revision: string; binary?: boolean; tooLarge?: boolean }
type Action = { kind: 'create-file' | 'create-dir' } | { kind: 'rename' | 'trash'; entry: Entry } | { kind: 'edit' };
const failureMessage = (failure: unknown) => userError(failure instanceof Error ? failure.message : String(failure));

/** On-demand real files, beside the workspace's chat list. No model or agent is needed. */
export function WorkspaceFiles({ workspace, hidden = false }: { workspace: { id: string; name: string; path: string }; hidden?: boolean }) {
    const [expanded, setExpanded] = useState(false);
    const [directory, setDirectory] = useState('');
    const [listing, setListing] = useState<Listing | null>(null);
    const [refresh, setRefresh] = useState(0);
    const [loading, setLoading] = useState(false);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const [action, setAction] = useState<Action | null>(null);
    const [name, setName] = useState('');
    const [document, setDocument] = useState<Document | null>(null);
    const [text, setText] = useState('');
    const [undo, setUndo] = useState<{ trashId: string; path: string } | null>(null);
    const id = useId();
    const query = `root=${encodeURIComponent(workspace.id)}`;
    const dirty = action?.kind === 'edit' && document && text !== document.text;
    const editable = document && !document.binary && !document.tooLarge;
    const filePath = (leaf: string) => directory ? `${directory}/${leaf}` : leaf;
    const reload = () => setRefresh(value => value + 1);

    useEffect(() => {
        if (!expanded) return;
        const controller = new AbortController();
        setLoading(true); setError(''); setListing(null);
        void api.get<Listing>(`/api/workspace/entries?${query}&path=${encodeURIComponent(directory)}`, controller.signal)
            .then(value => { if (!controller.signal.aborted) setListing(value); }, (failure: unknown) => { if (!controller.signal.aborted) setError(failureMessage(failure)); })
            .finally(() => { if (!controller.signal.aborted) setLoading(false); });
        return () => controller.abort();
    }, [expanded, directory, workspace.id, workspace.path, refresh, query]);

    async function run(operation: () => Promise<void>) {
        setBusy(true); setError('');
        try { await operation(); }
        catch (failure) { setError(failureMessage(failure)); }
        finally { setBusy(false); }
    }
    function close() { if (!busy && !dirty) setAction(null); }
    function newItem(kind: 'create-file' | 'create-dir') { setName(''); setText(''); setError(''); setAction({ kind }); }
    async function read(path: string) {
        await run(async () => {
            const value = await api.get<Document>(`/api/workspace/file?${query}&path=${encodeURIComponent(path)}`);
            setDocument(value); setText(value.text); setAction({ kind: 'edit' });
        });
    }
    async function save() {
        if (!action) return;
        await run(async () => {
            if (action.kind === 'edit' && document) {
                const value = await api.put<Document>('/api/workspace/file', { root: workspace.id, path: document.path, text, revision: document.revision });
                setDocument(value); setText(value.text);
            } else if (action.kind === 'create-file' || action.kind === 'create-dir') {
                await api.post('/api/workspace/file', { root: workspace.id, path: filePath(name.trim()), text, kind: action.kind === 'create-dir' ? 'dir' : 'file' });
                setAction(null);
            } else if (action.kind === 'rename') {
                const parent = action.entry.path.split('/').slice(0, -1).join('/');
                await api.patch('/api/workspace/file', { root: workspace.id, path: action.entry.path, newPath: parent ? `${parent}/${name.trim()}` : name.trim(), revision: action.entry.revision });
                setAction(null);
            } else if (action.kind === 'trash') {
                const item = await api.del<{ trashId: string; path: string }>(`/api/workspace/file?${query}&path=${encodeURIComponent(action.entry.path)}&revision=${encodeURIComponent(action.entry.revision)}`);
                setUndo(item); setAction(null);
            }
            reload();
        });
    }
    const title = action?.kind === 'edit' ? tr('File: {0}', [document?.path ?? ''])
        : action?.kind === 'create-file' ? tr('New file') : action?.kind === 'create-dir' ? tr('New folder')
        : action?.kind === 'rename' ? tr('Rename item') : tr('Move to workspace trash?');

    return <section className="workspace-files" style={hidden ? { display: 'none' } : undefined} aria-label={tr('Files in {0}', [workspace.name])}>
        <button type="button" className="workspace-files__toggle" aria-expanded={expanded} onClick={() => setExpanded(value => !value)}>
            <Icon name="chevron" size={14} className={expanded ? 'is-open' : ''}/><Icon name="file" size={16}/><span>{tr('Files')}</span>
        </button>
        {expanded ? <div className="workspace-files__body">
            <div className="workspace-files__toolbar">
                {directory ? <IconBtn name="chevron" title={tr('Parent folder')} disabled={busy} onClick={() => setDirectory(directory.split('/').slice(0, -1).join('/'))}/> : null}
                <span className="small muted workspace-files__path" title={workspace.path + '/' + directory}>{directory || workspace.name}</span>
                <IconBtn name="folder" title={tr('Open in app')} disabled={busy} onClick={() => void run(async () => { await api.post('/api/workspace/open', { root: workspace.id, path: directory }); })}/>
                <IconBtn name="file" title={tr('New file')} disabled={busy} onClick={() => newItem('create-file')}/>
                <IconBtn name="folder-plus" title={tr('New folder')} disabled={busy} onClick={() => newItem('create-dir')}/>
                <IconBtn name="refresh" title={tr('Refresh files')} disabled={loading || busy} onClick={reload}/>
            </div>
            {loading ? <p className="small muted" role="status">{tr('Loading files…')}</p> : null}
            {!loading && !listing?.entries.length ? <p className="small muted">{tr('This folder is empty.')}</p> : null}
            <ul className="workspace-files__list">
                {listing?.entries.map(entry => <li className="workspace-files__entry" key={entry.path}>
                    <button type="button" className="workspace-files__item" title={entry.path} disabled={busy} onClick={() => entry.kind === 'dir' ? setDirectory(entry.path) : void read(entry.path)}>
                        <Icon name={entry.kind === 'dir' ? 'folder' : 'file'} size={15}/><span>{entry.name}</span>
                    </button>
                    <IconBtn name="pencil" title={tr('Rename {0}', [entry.name])} disabled={busy} onClick={() => { setName(entry.name); setError(''); setAction({ kind: 'rename', entry }); }}/>
                    <IconBtn name="trash" title={tr('Move {0} to trash', [entry.name])} disabled={busy} onClick={() => { setError(''); setAction({ kind: 'trash', entry }); }}/>
                </li>)}
            </ul>
            {listing?.nextOffset != null ? <Btn size="sm" disabled={busy} onClick={() => void run(async () => {
                const next = await api.get<Listing>(`/api/workspace/entries?${query}&path=${encodeURIComponent(directory)}&offset=${listing.nextOffset}`);
                setListing({ ...next, entries: [...listing.entries, ...next.entries] });
            })}>{tr('Show more files')}</Btn> : null}
            {undo ? <div className="workspace-files__undo" role="status"><span className="small">{tr('Moved to workspace trash.')}</span><Btn size="sm" disabled={busy} onClick={() => void run(async () => {
                await api.post('/api/workspace/trash', { root: workspace.id, trashId: undo.trashId }); setUndo(null); reload();
            })}>{tr('Undo')}</Btn></div> : null}
            {error && !action ? <p role="alert" className="workspace-files__error small">{tr(error)} <Btn size="sm" onClick={reload}>{tr('Refresh files')}</Btn></p> : null}
        </div> : null}
        <Dialog open={!!action} wide={action?.kind === 'edit' || action?.kind === 'create-file'} compact={action?.kind === 'rename' || action?.kind === 'trash' || action?.kind === 'create-dir'}
            title={title} onClose={close} noClose={busy || !!dirty} actions={<>
                <Btn disabled={busy} onClick={() => setAction(null)}>{tr(dirty ? 'Discard changes' : 'Close')}</Btn>
                {action?.kind === 'edit' ? <><Btn disabled={busy} onClick={() => document && void run(async () => { await api.post('/api/workspace/open', { root: workspace.id, path: document.path }); })}>{tr('Open in app')}</Btn>
                    <Btn disabled={busy} onClick={() => document && void read(document.path)}>{tr('Reload file')}</Btn></> : null}
                {action?.kind !== 'edit' || editable ? <Btn variant={action?.kind === 'trash' ? 'danger' : 'primary'} disabled={busy || (action?.kind === 'edit' ? !dirty : action?.kind !== 'trash' && !name.trim())} onClick={() => void save()}>{tr(busy ? 'Saving…' : action?.kind === 'trash' ? 'Move to trash' : 'Save')}</Btn> : null}
            </>}>
            <p className="small muted workspace-files__path">{workspace.name} / {action?.kind === 'edit' ? document?.path : directory}</p>
            {action?.kind === 'create-file' || action?.kind === 'create-dir' || action?.kind === 'rename' ? <label className="input-field" htmlFor={id + '-name'}><span>{tr('File or folder name')}</span><input id={id + '-name'} className="st-input" autoFocus value={name} onChange={event => setName(event.target.value)} disabled={busy}/></label> : null}
            {action?.kind === 'edit' && !editable ? <p>{tr('This file cannot be edited as text. Use Open in app.')}</p> : null}
            {action?.kind === 'create-file' || action?.kind === 'edit' && editable ? <label className="input-field" htmlFor={id + '-text'}><span>{tr('File contents')}</span><textarea id={id + '-text'} className="st-input workspace-files__editor" value={text} disabled={busy} spellCheck={false} onChange={event => setText(event.target.value)}/></label> : null}
            {dirty ? <p className="small" role="status">{tr('Unsaved changes')}</p> : null}
            {action?.kind === 'trash' ? <p>{tr('Move {0} to workspace trash? You can undo this.', [action.entry.name])}</p> : null}
            {error ? <p role="alert" className="workspace-files__error">{tr(error)}</p> : null}
        </Dialog>
    </section>;
}
