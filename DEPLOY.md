# Put PlainSpeak online (free, about 5 minutes)

You need: the GitHub account that owns the repo (KrypticStudios) and your free Gemini key from https://aistudio.google.com.

1. Go to **https://share.streamlit.io** and click **Continue with GitHub**. Sign in as KrypticStudios and allow access.
2. Click **Create app** → **Deploy a public app from GitHub**.
3. Fill in:
   - **Repository:** `KrypticStudios/plainspeak`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** choose a name, e.g. `plainspeak-evohacks`
4. Click **Advanced settings**:
   - **Python version:** `3.12`
   - **Secrets:** paste this, with your real key between the quotes:
     ```toml
     GEMINI_API_KEY = "paste-your-key-here"
     ```
   - Do **not** add `PLAINSPEAK_LOCAL`. Leaving it out keeps saved letters out of the server's storage.
5. Click **Deploy**. The first build takes 2–4 minutes.
6. Open the link and try an example letter, then a photo of one of the sample letters on your screen.

**Never** put the key in the code or a GitHub file. The Secrets box is private.

## If something goes wrong
- **"No AI model was available":** in Secrets, add a line `GEMINI_MODEL = "..."` with a model name from AI Studio's model list, then click **Reboot app**.
- **"The free AI limit was reached":** wait a minute. The free tier has per-minute limits.
- **The app is "asleep":** free apps sleep after a while with no visitors. Click **Yes, get this app back up**, and wake it before judging starts.
- **To change the key:** go to app ⋮ → **Settings** → **Secrets**.
