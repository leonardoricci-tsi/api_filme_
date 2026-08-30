import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { DetalhesFilme, PaginaFilmes } from '../../models/movie.model';

@Injectable({ providedIn: 'root' })
export class MoviesService {
  constructor(private readonly http: HttpClient) {}

  listar(pagina = 1, busca = ''): Observable<PaginaFilmes> {
    const params: Record<string, string | number> = { pagina };
    if (busca) {
      params['busca'] = busca;
    }
    return this.http.get<PaginaFilmes>('/movies', { params });
  }

  detalhes(tmdbMovieId: number): Observable<DetalhesFilme> {
    return this.http.get<DetalhesFilme>(`/movies/${tmdbMovieId}/detalhes`);
  }
}
