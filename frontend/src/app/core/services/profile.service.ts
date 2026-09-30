import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

import { Profile } from '../../models/profile.model';

@Injectable({ providedIn: 'root' })
export class ProfileService {
  // Foto do usuário LOGADO, compartilhada com o avatar do header (que
  // aparece em todas as telas). Toda resposta do próprio perfil atualiza
  // esse signal — assim trocar a foto reflete no header na hora, sem reload.
  private readonly _minhaFotoUrl = signal<string | null>(null);
  readonly minhaFotoUrl = this._minhaFotoUrl.asReadonly();

  constructor(private readonly http: HttpClient) {}

  carregarMinhaFoto(usuarioId: number): void {
    this.ver(usuarioId).subscribe({ error: () => this._minhaFotoUrl.set(null) });
  }

  limparMinhaFoto(): void {
    this._minhaFotoUrl.set(null);
  }

  ver(usuarioId: number): Observable<Profile> {
    return this.http.get<Profile>(`/profiles/${usuarioId}`).pipe(tap((p) => this.lembrarSeForMeu(p)));
  }

  editarBio(usuarioId: number, bio: string): Observable<Profile> {
    return this.http
      .patch<Profile>(`/profiles/${usuarioId}`, { bio })
      .pipe(tap((p) => this.lembrarSeForMeu(p)));
  }

  enviarFoto(usuarioId: number, arquivo: File): Observable<Profile> {
    // Sem Content-Type manual: o navegador monta o multipart/form-data com
    // o boundary certo sozinho — setar na mão quebra o upload.
    const corpo = new FormData();
    corpo.append('arquivo', arquivo);
    return this.http
      .post<Profile>(`/profiles/${usuarioId}/foto`, corpo)
      .pipe(tap((p) => this.lembrarSeForMeu(p)));
  }

  private lembrarSeForMeu(perfil: Profile): void {
    // A URL é pré-assinada e expira (15 min), mas uma <img> que já carregou
    // continua exibida; cada nova leitura do próprio perfil renova a URL.
    if (perfil.eh_meu) {
      this._minhaFotoUrl.set(perfil.foto_url);
    }
  }
}
