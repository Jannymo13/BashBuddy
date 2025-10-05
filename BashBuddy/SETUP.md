# BashBuddy First-Run Setup

## After Installation

After installing BashBuddy with `pip install bashbuddy` or `pip install dist/*.whl`, you need to set up your API keys.

## Setup Steps

### 1. Create Configuration Directory

BashBuddy stores its configuration in `~/.bashbuddy/`:

```bash
mkdir -p ~/.bashbuddy
```

### 2. Create Environment File

Create `~/.bashbuddy/.env` with your API keys:

```bash
cat > ~/.bashbuddy/.env << 'EOF'
# Required: Get your API key from https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: For usage analytics
# Get these from https://supabase.com/dashboard
# SUPABASE_URL=your_supabase_url
# SUPABASE_KEY=your_supabase_anon_key
EOF
```

### 3. Add Your Gemini API Key

Edit the file and replace `your_gemini_api_key_here` with your actual key:

```bash
nano ~/.bashbuddy/.env
# or
vim ~/.bashbuddy/.env
```

### 4. Test the Installation

```bash
bb ask "list files"
```

## Alternative: Use Project-Local .env

You can also create a `.env` file in your current working directory:

```bash
# In your project directory
cat > .env << 'EOF'
GEMINI_API_KEY=your_gemini_api_key_here
EOF
```

BashBuddy searches for `.env` in this order:
1. Current working directory: `./.env`
2. BashBuddy config directory: `~/.bashbuddy/.env`
3. Installation directory (not recommended)

## Getting Your Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and paste it into your `.env` file

## Optional: Supabase Setup

If you want usage tracking:

1. Create account at [Supabase](https://supabase.com/)
2. Create a new project
3. Go to Project Settings → API
4. Copy the URL and anon key
5. Add to `~/.bashbuddy/.env`:
   ```
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=eyJxxx...
   ```

## Verification

Check that BashBuddy can find your configuration:

```bash
# This should show the daemon log
cat ~/.bashbuddy/daemon.log

# Should see a line like:
# "Loaded .env from: /home/user/.bashbuddy/.env"
```

## Troubleshooting

### "GEMINI_API_KEY not found"

- Make sure you created `~/.bashbuddy/.env`
- Make sure the file contains `GEMINI_API_KEY=...` (no quotes around the value)
- Check for typos in the variable name
- Make sure there are no spaces around the `=` sign

### "Command logging disabled"

This is normal if you don't have Supabase configured. Command logging is optional.

### Daemon Won't Start

1. Check the log file: `cat ~/.bashbuddy/daemon.log`
2. Make sure Python 3.13+ is installed: `python3 --version`
3. Try stopping and restarting: `bb stop && bb start`

### Need Help?

Open an issue on [GitHub](https://github.com/Jannymo13/bashbuddy/issues)
