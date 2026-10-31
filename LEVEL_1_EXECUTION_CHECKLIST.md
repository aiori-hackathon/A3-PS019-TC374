# AIORI 3 Hackathon - Level 1 Evaluation Action Plan (Steps 1 – 7)

> **Deadline:** **October 14, 2026** (Required to qualify for Level 2 Certificate & Evaluation)  
> **Problem Statement:** **PS-019: Personal-Data Discovery and Privacy Evidence Inventory**  
> **Team Reference:** Check your exact Team Code (e.g. `A3-PS019-TCXXX`) on the [Selected Teams Portal](https://portal.aiori.in/aiori-3/selected-teams/)

---

## ⚠️ Critical Notice from Organizers (Email from Anupam Agrawal)

> **DO NOT FORK THE TEMPLATE REPOSITORY!**  
> If you fork the repository, GitHub will trigger this error during ownership transfer:  
> *“aiori-hackathon already has a repository in the aiori-hackathon/A3-PSXXX-TCXXX network.”*  
> 
> **Correct Method:** You MUST click **"Use this template"** on the official template repository.

---

## 📋 Step-by-Step Level 1 Submission Checklist (Step 1 to Step 7)

### ✅ Step 1: Create Team Repository from Official Template
1. Open the official template repository:
   👉 **[https://github.com/aiori-hackathon/A3-PSXXX-TCXXX](https://github.com/aiori-hackathon/A3-PSXXX-TCXXX)**
2. Click the green button: **"Use this template"** ➔ **"Create a new repository"**.
3. **DO NOT click Fork.**

---

### ✅ Step 2: Name Repository Using Team Code & Add Teammates
1. Find your official **Team Code** on the [AIORI Selected Teams List](https://portal.aiori.in/aiori-3/selected-teams/) (Format: `A3-PS019-TCXXX`).
2. Set the **Repository name** to your exact Team Code (e.g., `A3-PS019-TC006` or your assigned code).
3. Set visibility to **Private**.
4. Click **Create repository**.
5. In your new repository, go to **Settings** ➔ **Collaborators** ➔ **Add people** ➔ add all your team members. Ensure everyone accepts their invitation.

---

### ✅ Step 3: Add `aiori-hackathon` as Collaborator
1. In your team repository on GitHub, go to **Settings** ➔ **Collaborators** (left sidebar under Access).
2. Click **Add people**.
3. In the search box, enter:
   ```
   aiori-hackathon
   ```
   (Direct Profile: [https://github.com/aiori-hackathon](https://github.com/aiori-hackathon))
4. Click **Add aiori-hackathon to this repository**.
5. Wait for the invitation status to show as accepted by `aiori-hackathon`.

---

### ✅ Step 4: Transfer Repository Ownership to `aiori-hackathon`
Once all teammates and `aiori-hackathon` have accepted collaborator invites:
1. Go to **Settings** in your repository.
2. Scroll to the very bottom to the **Danger Zone** section.
3. Click **Transfer ownership**.
4. In the prompt:
   - **New owner's username or organization:** `aiori-hackathon`
   - Type the repository name to confirm.
5. Click **I understand, transfer this repository**.

---

### ✅ Step 5: Upload Proposal Presentation (`Proposed-structure-hackathon.pdf`)
Your repository must contain the PDF file in the root folder named:
```
Proposed-structure-hackathon.pdf
```
> **Status:** **ALREADY GENERATED & COMMITTED!**  
> We have pre-compiled this file in your workspace using ReportLab, strictly structured to match the 5 mandatory sections:
> 1. *Problem Description*
> 2. *Solution Proposed*
> 3. *Optimization Proposed by the Team*
> 4. *Solution Architecture and Design*
> 5. *Implementation Details & Prototype Demonstration (Pseudocode)*

---

### ✅ Step 6: Push Full Source Code & Documentation to Your Repository
Link your local project directory (`c:\Users\jenij\Desktop\Hackathon`) to your newly created GitHub repository and push:

```powershell
# Open terminal in c:\Users\jenij\Desktop\Hackathon

# 1. Add your GitHub remote URL (replace YOUR-TEAM-CODE with your repo name)
git remote add origin https://github.com/<YOUR-GITHUB-USERNAME>/<YOUR-TEAM-CODE>.git

# 2. Push all code, data, and the PDF to main branch
git branch -M main
git push -u origin main
```

---

### ✅ Step 7: Prototype Demonstration with Pseudocode to Mentors
Prepare for mentor evaluation sessions:
1. **Annotated Algorithm Pseudocode:** Located in [`PSEUDOCODE_AND_DEMO_GUIDE.md`](file:///c:/Users/jenij/Desktop/Hackathon/PSEUDOCODE_AND_DEMO_GUIDE.md).
2. **Terminal Demo Command:**
   ```powershell
   python cli.py evaluate
   ```
   Shows **95.4% Macro F1**, **100% Precision** on Direct Identifiers & Government IDs, and **93.94% Non-PII Negative Specificity**.
3. **Interactive Web Dashboard Demo:**
   ```powershell
   python web/app.py
   ```
   Open `http://127.0.0.1:5000` to showcase live discovery scanning, the shadow data gap report, and the legal boundary disclaimer.

---

## 📞 Key Contacts & Resources
- **Submission Guidelines:** [https://portal.aiori.in/aiori-3/hackathon-guideline/](https://portal.aiori.in/aiori-3/hackathon-guideline/)
- **Selected Teams Portal:** [https://portal.aiori.in/aiori-3/selected-teams/](https://portal.aiori.in/aiori-3/selected-teams/)
- **Program Manager:** Arnab Das (`arnab.d@iifon.net`, +91 9007958380)
- **AIORI Team / Support:** Anupam Agrawal (`anupam@iifon.net`, +91 90517 03611 / `aiori@iifon.net`)
