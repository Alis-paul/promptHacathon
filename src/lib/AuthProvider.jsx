import React, { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from './supabase';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null); // Supabase auth user
  const [profile, setProfile] = useState(null); // Row from profiles table
  const [sessionLoading, setSessionLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  // Listen for auth changes
  useEffect(() => {
    const { data: listener } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (session?.user) {
        setUser(session.user);
        await fetchProfile(session.user.id);
      } else {
        setUser(null);
        setProfile(null);
      }
    });
    // Initial check
    const init = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.user) {
        setUser(session.user);
        await fetchProfile(session.user.id);
      } else {
        setUser(null);
        setProfile(null);
      }
      setSessionLoading(false);
    };
    init();
    return () => {
      listener?.unsubscribe();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchProfile = async (userId) => {
    const { data, error } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', userId)
      .single();
    if (error) {
      console.error('Failed to fetch profile', error);
      setProfile(null);
    } else {
      setProfile(data);
    }
  };

  const signIn = async (email, password) => {
    setAuthError(null);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) {
      // Map supabase errors to friendly messages
      if (error.message.includes('Invalid login credentials')) {
        setAuthError('Invalid email or password.');
      } else {
        setAuthError('Your account could not be authenticated.');
      }
    }
    // onAuthStateChange will update user/profile automatically
  };

  const signUp = async (email, password, fullName, phone) => {
    setAuthError(null);
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
          phone: phone,
        },
      },
    });
    if (error) {
      if (error.message.includes('already registered')) {
        setAuthError('An account with this email already exists.');
      } else {
        setAuthError('Registration failed. Please try again later.');
      }
    }
    // Trigger creates profile via DB trigger; we will fetch after sign‑in
  };

  const signOut = async () => {
    await supabase.auth.signOut();
    setUser(null);
    setProfile(null);
  };

  const value = {
    user,
    profile,
    sessionLoading,
    authError,
    signIn,
    signUp,
    signOut,
    setAuthError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => useContext(AuthContext);
