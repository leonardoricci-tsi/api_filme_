import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { Profile } from '../../models/profile.model';

@Injectable({ providedIn: 'root' })
export class ProfileService {
  constructor(private readonly http: HttpClient) {}

  ver(usuarioId: number): Observable<Profile> {
    return this.http.get<Profile>(`/profiles/${usuarioId}`);
  }

  editarBio(usuarioId: number, bio: string): Observable<Profile> {
    return this.http.patch<Profile>(`/profiles/${usuarioId}`, { bio });
  }

  enviarFoto(usuarioId: number, arquivo: File): Observable<Profile> {
    // Sem Content-Type manual: o navegador monta o multipart/form-data com
    // o boundary certo sozinho — setar na mão quebra o upload.
    const corpo = new FormData();
    corpo.append('arquivo', arquivo);
    return this.http.post<Profile>(`/profiles/${usuarioId}/foto`, corpo);
  }
}
