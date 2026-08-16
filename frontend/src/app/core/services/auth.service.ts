import { Injectable, computed, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, switchMap, tap } from 'rxjs';

import { LoginPayload, RegisterPayload, TokenResponse } from '../../models/auth.model';

const TOKEN_KEY = 'token';
const NOME_KEY = 'nome';
const EMAIL_KEY = 'email';

export interface UsuarioLogado {
  nome: string;
  email: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly _token = signal<string | null>(localStorage.getItem(TOKEN_KEY));
  private readonly _usuario = signal<UsuarioLogado | null>(this.lerUsuarioSalvo());

  readonly isAuthenticated = computed(() => this._token() !== null);
  readonly usuario = this._usuario.asReadonly();

  constructor(private readonly http: HttpClient) {}

  private lerUsuarioSalvo(): UsuarioLogado | null {
    const nome = localStorage.getItem(NOME_KEY);
    const email = localStorage.getItem(EMAIL_KEY);
    return nome && email ? { nome, email } : null;
  }

  getToken(): string | null {
    return this._token();
  }

  login(payload: LoginPayload): Observable<UsuarioLogado> {
    return this.http.post<TokenResponse>('/auth/login', payload).pipe(
      tap((resposta) => this._token.set(resposta.access_token)),
      tap((resposta) => localStorage.setItem(TOKEN_KEY, resposta.access_token)),
      switchMap(() => this.carregarPerfil()),
    );
  }

  register(payload: RegisterPayload): Observable<UsuarioLogado> {
    return this.http.post<TokenResponse>('/auth/register', payload).pipe(
      tap((resposta) => this._token.set(resposta.access_token)),
      tap((resposta) => localStorage.setItem(TOKEN_KEY, resposta.access_token)),
      switchMap(() => this.carregarPerfil()),
    );
  }

  private carregarPerfil(): Observable<UsuarioLogado> {
    return this.http.get<UsuarioLogado>('/auth/me').pipe(
      tap((usuario) => {
        localStorage.setItem(NOME_KEY, usuario.nome);
        localStorage.setItem(EMAIL_KEY, usuario.email);
        this._usuario.set(usuario);
      }),
    );
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(NOME_KEY);
    localStorage.removeItem(EMAIL_KEY);
    this._token.set(null);
    this._usuario.set(null);
  }
}
