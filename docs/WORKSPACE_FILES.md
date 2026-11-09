# Files in a workspace

The local candidate includes a Files section below the chats in each left-sidebar
workspace. It reads the folder on disk, including files that existed before you
used Strata. Open Files to browse. Open a folder to see its contents. Refresh files
reads changes made by another program; Show more files opens the next page.

Use New file or New folder to create an item in the folder you are viewing. Click
a text file to open the editor, then use Save. The editor supports UTF-8 text up
to 200 KiB. Other files can be opened in their own application with Open in app.
The folder button opens the current folder in the system file manager.

The pencil beside an item renames it. The trash button moves the item into
`.strata-trash` inside that workspace. Undo restores the most recently moved item.
The contents remain on disk, and Strata does not automatically empty this folder.
An item is not restored over another file with the same name.

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
