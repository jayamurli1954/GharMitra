# 🔗 How to Get Supabase Database Connection String

Step-by-step guide to find your Supabase database connection string.

---

## 📍 Method 1: Using the "Connect" Button (Easiest)

1. **Open your Supabase project dashboard**
   - Go to [supabase.com](https://supabase.com)
   - Select your project

2. **Click "Connect" button**
   - Look in the left sidebar for **"Connect"** button
   - OR look for a **"Connect"** button in the project overview page
   - OR click the **"Connect"** tab at the top

3. **Find the Connection String section**
   - You'll see different connection options:
     - **Direct connection** (for servers/VMs)
     - **Session mode** (for persistent connections)
     - **Transaction mode** (for serverless)

4. **Select "Direct connection" or "URI"**
   - Click on the **"URI"** tab or **"Direct connection"** option
   - You'll see a connection string like:
     ```
     postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
     ```

5. **Copy the connection string**
   - Click the copy icon next to the connection string
   - Or manually select and copy it

6. **Replace the password placeholder**
   - The string will have `[YOUR-PASSWORD]` as a placeholder
   - Replace it with your actual database password (the one you set when creating the project)

---

## 📍 Method 2: Through Project Settings

1. **Go to Project Settings**
   - Click the **gear icon (⚙️)** in the left sidebar
   - OR click **"Project Settings"** from the dropdown menu

2. **Navigate to Database**
   - In the settings menu, click **"Database"**

3. **Find Connection String**
   - Scroll down to find **"Connection string"** or **"Connection info"** section
   - Look for **"URI"** or **"Connection string"** option

4. **Copy the connection string**
   - It will be in this format:
     ```
     postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
     ```

5. **Replace password placeholder**
   - Replace `[YOUR-PASSWORD]` with your actual password

---

## 📍 Method 3: If You Can't Find It

1. **Check the Database Overview**
   - In your project dashboard, look for **"Database"** section
   - Click on it to see database details

2. **Look for Connection Info**
   - You might see connection details in the database overview
   - Look for hostname, port, database name

3. **Manually Construct Connection String**
   - If you can see the hostname, you can construct it manually:
     ```
     postgresql://postgres:YOUR_PASSWORD@HOSTNAME:5432/postgres
     ```
   - Example:
     ```
     postgresql://postgres:MyPassword123@db.abcdefghijklmnop.supabase.co:5432/postgres
     ```

---

## 🔑 Finding Your Database Password

If you forgot your database password:

1. Go to **Project Settings** → **Database**
2. Look for **"Database Password"** section
3. Click **"Reset database password"** or **"Generate new password"**
4. **Save the new password** - you'll need to update your connection string

---

## ✅ Verify Your Connection String

Your connection string should look like:

```
postgresql://postgres:YourActualPassword@db.xxxxx.supabase.co:5432/postgres
```

**Components:**
- `postgresql://` - Protocol
- `postgres` - Username (default)
- `YourActualPassword` - Your database password (no brackets)
- `db.xxxxx.supabase.co` - Your Supabase hostname
- `5432` - Port (default PostgreSQL port)
- `postgres` - Database name (default)

---

## 🚨 Common Issues

### Issue: "I can't find the Connect button"
**Solution:**
- Make sure you're logged into Supabase
- Make sure your project is fully provisioned (wait 2-3 minutes after creation)
- Try refreshing the page
- Look for "Database" in the left sidebar instead

### Issue: "The connection string has [YOUR-PASSWORD] placeholder"
**Solution:**
- This is normal! You need to manually replace `[YOUR-PASSWORD]` with your actual password
- The password is the one you set when creating the project
- If you forgot it, reset it in Project Settings → Database

### Issue: "I see multiple connection strings"
**Solution:**
- For Railway deployment, use the **"Direct connection"** or **"URI"** format
- Don't use "Pooler" or "Transaction mode" for initial setup
- The direct connection looks like: `postgresql://postgres:...@db.xxxxx.supabase.co:5432/postgres`

---

## 📸 Visual Guide Locations

The connection string is typically found in one of these locations:

1. **Left Sidebar** → **"Connect"** button
2. **Top Navigation** → **"Connect"** tab
3. **Project Settings** (⚙️) → **"Database"** → **"Connection string"**
4. **Database Overview** → **"Connection info"**

---

## ✅ Checklist

- [ ] Found the connection string
- [ ] Copied the connection string
- [ ] Replaced `[YOUR-PASSWORD]` with actual password
- [ ] Verified the format is correct
- [ ] Saved the connection string securely
- [ ] Ready to use in Railway environment variables

---

**Need more help?** Check the Supabase documentation: [supabase.com/docs/guides/database/connecting-to-postgres](https://supabase.com/docs/guides/database/connecting-to-postgres)
