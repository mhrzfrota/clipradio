import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from 'react';
import apiClient from '@/lib/apiClient';
import { useToast } from '@/components/ui/use-toast';

const AuthContext = createContext(undefined);

export const AuthProvider = ({ children }) => {
  const { toast } = useToast();

  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const getSession = async () => {
      try {
        const token = localStorage.getItem('auth_token');
        if (!token) {
          setLoading(false);
          return;
        }

        const userData = await apiClient.getMe();
        setUser(userData);
      } catch (err) {
        console.error('Erro ao obter sessão:', err);
        localStorage.removeItem('auth_token');
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    getSession();
  }, []);

  const signUp = useCallback(async (email, password, nome) => {
    try {
      const data = await apiClient.register(email, password, nome);
      setUser(data.user);
      return { error: null };
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Falha no Cadastro",
        description: error.message || "Algo deu errado. Tente novamente.",
      });
      return { error };
    }
  }, [toast]);

  const signIn = useCallback(async (email, password) => {
    try {
      const data = await apiClient.login(email, password);
      setUser(data.user);
      return { error: null };
    } catch (error) {
      console.error('Erro no login:', error);
      toast({
        variant: "destructive",
        title: "Falha no Login",
        description: error.message || "Algo deu errado. Verifique suas credenciais.",
      });
      return { error };
    }
  }, [toast]);

  const signOut = useCallback(async () => {
    try {
      await apiClient.logout();
      setUser(null);
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Erro ao sair",
        description: error.message || "Algo deu errado.",
      });
    }
  }, [toast]);

  const value = useMemo(() => ({
    user,
    session: user ? { user } : null,
    loading,
    signUp,
    signIn,
    signOut,
  }), [user, loading, signUp, signIn, signOut]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

