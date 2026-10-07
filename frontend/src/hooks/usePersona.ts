import { usePersonaContext } from '@/providers/PersonaProvider';

export const usePersona = () => {
  return usePersonaContext();
};
