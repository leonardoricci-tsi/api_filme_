import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { Favorite, FavoritePayload } from '../../models/favorite.model';

@Injectable({ providedIn: 'root' })
export class FavoritesService {
  constructor(private readonly http: HttpClient) {}

  listar(): Observable<Favorite[]> {
    return this.http.get<Favorite[]>('/favorites');
  }

  criar(payload: FavoritePayload): Observable<Favorite> {
    return this.http.post<Favorite>('/favorites', payload);
  }

  remover(id: number): Observable<void> {
    return this.http.delete<void>(`/favorites/${id}`);
  }
}
