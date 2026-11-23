# CivicAssist Authentication and Role System

This file documents the steps required to set up Supabase Auth, the front‑end authentication flow, and role‑based routing for CivicAssist.

## 1. Environment variables (frontend)
Create a `.env` file (do **not** commit it) with the following VITE‑prefixed keys:
```
VITE_SUPABASE_URL=https://<your‑project>.supabase.co
VITE_SUPABASE_ANON_KEY=<your‑anon‑public‑key>
```
The `.env.example` already contains placeholder values.

## 2. Supabase client (`src/lib/supabase.js`)
```javascript
import { createClient } from "@supabase/supabase-js";

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);
```

## 3. Auth context (`src/lib/AuthProvider.jsx`)
Provides `useAuth()` hook exposing:
- `user` (Supabase auth user)
- `profile` (row from `profiles` table)
- `sessionLoading` flag
- `signIn`, `signUp`, `signOut` helpers.

## 4. Pages
- `src/pages/Login.jsx`
- `src/pages/Register.jsx`
- `src/pages/Unauthorized.jsx`
- Placeholder dashboards:
  - `src/pages/CitizenDashboard.jsx`
  - `src/pages/DepartmentDashboard.jsx`
  - `src/pages/AdminDashboard.jsx`

## 5. Routing (`src/App.jsx`)
Uses `react-router-dom`:
```jsx
<BrowserRouter>
  <AuthProvider>
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route element={<ProtectedRoute allowedRoles={["citizen"]} />}>
        <Route path="/citizen/*" element={<CitizenDashboard />} />
      </Route>
      <Route element={<ProtectedRoute allowedRoles={["department"]} />}>
        <Route path="/department/*" element={<DepartmentDashboard />} />
      </Route>
      <Route element={<ProtectedRoute allowedRoles={["admin"]} />}>
        <Route path="/admin/*" element={<AdminDashboard />} />
      </Route>
      <Route path="*" element={<Unauthorized />} />
    </Routes>
  </AuthProvider>
</BrowserRouter>
```
`ProtectedRoute` checks auth state and role, redirects to `/login` if unauthenticated or to `/unauthorized` if role mismatch.

## 6. Navigation (`src/components/Navigation.jsx`)
Updated to show:
- Logged‑out: **Login**, **Report an Issue** (link to `/register`)
- Logged‑in: **Dashboard** (role‑specific URL), **Notifications**, **Profile**, **Logout**

## 7. Profile creation on registration
The front‑end sign‑up calls `supabase.auth.signUp({ email, password }, { data: { full_name: name, phone } })`. Supabase stores `full_name` and `phone` in `raw_user_meta_data`. A **trigger** (`handle_new_user`) added in the migration (Phase 02) automatically creates a `profiles` row with `role = 'citizen'`.

## 8. Development accounts (admin & departments)
A one‑off script (`supabase/create_dev_accounts.js`) uses the **service‑role key** to:
1. Create a user via the Auth API (`supabase.auth.admin.createUser`).
2. Insert the corresponding `profiles` row with the correct `role` and `department_id`.
Run it locally with:
```bash
node supabase/create_dev_accounts.js
```
Only run this in a trusted environment; the script never commits passwords.

## 9. Security checklist
- Front‑end route guards for UX only.
- Supabase RLS policies (Phase 02) enforce that only the owner/role can access data.
- No role can be escalated from the client because the `profiles.role` column is never writable from the client side.
- All protected pages render a **loading** indicator while the session is being resolved.
- Errors from Supabase are mapped to user‑friendly messages.

---

**Next steps:** Implement the files referenced above.
