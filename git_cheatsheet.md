# 🚀 Git Commands Cheat Sheet for Hidden Nepal

## Branch Structure
- **main** → Production-ready stable code
- **develop** → Integration branch for testing features before main
- **auth** → Authentication blueprint
- **viewer** → Viewer/Visitor blueprint
- **contributor** → Contributor blueprint
- **admin** → Admin blueprint

---

## 🔹 1. Clone Repository
```bash
git clone <repo_url>
cd Hidden_nepal
```

---

## 🔹 2. Branch Management
```bash
git branch            # List local branches
git branch -r         # List remote branches
git checkout <branch> # Switch to branch
git checkout -b new-feature-branch develop # Create new branch from develop
```

---

## 🔹 3. Daily Workflow
```bash
git checkout auth          # switch to branch
git pull origin auth       # update with remote
# make changes...
git add .                  # stage changes
git commit -m "message"    # commit changes
git push origin auth       # push changes
```

---

## 🔹 4. Update Branch with Develop
```bash
git checkout auth
git pull origin develop        # merge develop into auth
# OR
git rebase origin/develop      # rebase for clean history
```

---

## 🔹 5. Merge Feature → Develop
```bash
git checkout develop
git pull origin develop
git merge auth
git push origin develop
```

---

## 🔹 6. Merge Develop → Main (Release)
```bash
git checkout main
git pull origin main
git merge develop
git push origin main
```

---

## 🔹 7. Check History
```bash
git log --oneline --graph --decorate --all
```

---

## 🔹 8. Undo / Fix Mistakes
```bash
git checkout -- <file>     # discard unstaged changes
git reset --hard HEAD~1    # undo last commit
git revert <commit_hash>   # safely undo a commit
```

---

⚡ **Workflow:**  
`auth/viewer/contributor/admin → develop → main`
