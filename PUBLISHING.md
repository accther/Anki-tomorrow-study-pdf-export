# Publishing Guide

This project is ready for two distribution channels:

- GitHub source repository
- AnkiWeb add-on listing

## 1. Package the add-on

AnkiWeb requires a `.ankiaddon` file whose top level contains the add-on files directly.
Do not include the outer folder name in the archive, and do not include any `__pycache__` folders.

Official references:

- https://addon-docs.ankiweb.net/sharing.html
- https://addon-docs.ankiweb.net/addon-folders.html

Run:

```bash
cd <repo-root>
chmod +x package_addon.sh
./package_addon.sh
```

Output:

```text
dist/tomorrow_pdf_export.ankiaddon
```

## 2. Publish to GitHub

Initialize the repository content and create the first commit:

```bash
cd <repo-root>
git add .
git commit -m "Initial release of Tomorrow Study PDF Export"
```

Create a GitHub repository, then add the remote and push:

```bash
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

Recommended GitHub release assets:

- Source code
- `dist/tomorrow_pdf_export.ankiaddon`

Recommended repository sections:

- Short description
- Screenshot(s)
- Compatibility note: tested with Anki 25.09.2 on macOS
- Known limitations: scheduler fallback and complex template rendering sensitivity

## 3. Publish to AnkiWeb

Official upload entry:

- https://ankiweb.net/shared/addons/

Official packaging note:

- https://addon-docs.ankiweb.net/sharing.html

Steps:

1. Sign in to your AnkiWeb account.
2. Open the add-on sharing page.
3. Click `Upload`.
4. Fill in the add-on title, description, and support URL.
5. Upload `dist/tomorrow_pdf_export.ankiaddon`.
6. Submit the listing.

Recommended support URL:

- Your GitHub repository URL
- Or your GitHub issues page

## 4. Suggested listing copy

### Title

Tomorrow Study PDF Export

### Short description

Export tomorrow's Anki study queue to a printable PDF, with deck filtering and scheduler-based ordering.

### Key features

- Select one or more decks
- Include child decks
- Preserve tomorrow's study order as closely as possible
- Split questions and answers for printing
- Suitable for paper practice before syncing results back into Anki

### Compatibility

- macOS
- Anki 25.09.2 tested

## 5. AnkiWeb account restrictions

Recent forum reports indicate some new accounts may be restricted from uploading add-ons.
That appears to be part of AnkiWeb's anti-abuse controls, not a packaging problem.

Reference:

- https://forums.ankiweb.net/t/account-too-new-to-upload-add-on/68440

Treat that as a platform policy signal, not an official developer API guarantee.
