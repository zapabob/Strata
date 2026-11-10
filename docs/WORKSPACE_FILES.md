# Files in a workspace

The local candidate includes a Files section below the chats in each left-sidebar
workspace. It reads the folder on disk, including files that existed before you
used Strata. Open Files to browse. Open a folder to see its contents. Refresh files
reads changes made by another program; Show more files opens the next page.

Use New file or New folder to create an item in the folder you are viewing. Click
a text file to open the editor, then use Save. The editor supports UTF-8 text up
to 200 KiB. Other files can be opened in their own application with Open in app.
The folder button opens the current folder in the system file manager.

Open an item's three-dot action menu to rename, move or delete it. Delete moves it into
`.strata-trash` inside that workspace. Undo restores the most recently moved item.
The contents remain on disk, and Strata does not automatically empty this folder.
An item is not restored over another file with the same name.

## Conversations in the left folder

The folder's three-dot menu includes **Delete all chats in folder**. Confirm the
folder name and chat count before deleting. It includes archived chats and chats
beyond the sidebar's first20 rows. Chats created after opening the confirmation
are excluded. Finish or stop running replies first. A failed deletion remains
visible; other folders and actual files are retained. Chat deletion is permanent,
unlike file trash. Use Archive chat when you want to restore a conversation later.

日本語表示では、左フォルダーの **… → フォルダー内の会話履歴をすべて削除**
を選び、対象件数を確認して削除します。キャンセルもできます。
会話の一括削除で、フォルダー内のファイルやモデルは削除しません。

If another editor changes a file while you are editing, Strata refuses to save
over that change. Keep your draft, or discard it and reload the file before trying
again. CRLF line endings and a UTF-8 byte-order marker are preserved when saving.
Previous text contents are retained in workspace trash when saved. Windows saves
use a metadata-preserving replacement, with merge errors treated as failures.

File actions apply to the selected, registered workspace. Linked files and
folders are not followed by this file manager. Git internals and workspace trash
are not normal editable entries. No model needs to be loaded to manage files.

This describes local candidate source. See `HAKUA_RELEASE.md` for the published
Windows release and its measured limits.
