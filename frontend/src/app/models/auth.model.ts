export interface RegisterPayload {
  nome: string;
  email: string;
  senha: string;
}

export interface LoginPayload {
  email: string;
  senha: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}
