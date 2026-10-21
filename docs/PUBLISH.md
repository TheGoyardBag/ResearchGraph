# Publish as a new repository

Run the tests, inspect the code and replace any prototype-only claims before using
this in a portfolio. Do not claim this was built at a past employer.

```bash
git init
git add .
git status
git commit -m "Initial ResearchGraph research prototype"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/researchgraph.git
git push -u origin main
```

Create an empty repository named `researchgraph` in your own GitHub account first.
Review `git status` before committing: no tokens, `.env`, state databases, imported
private data, virtual environments, or personal records should be tracked.
Keep the synthetic-data disclosure and model limitations visible. Upload source
files rather than a ZIP of the repository. No remote GitHub actions have been
performed on your behalf.
