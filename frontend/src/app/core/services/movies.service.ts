import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { Movie } from '../../models/movie.model';

@Injectable({ providedIn: 'root' })
export class MoviesService {
  constructor(private readonly http: HttpClient) {}

  listar(): Observable<Movie[]> {
    return this.http.get<Movie[]>('/movies');
  }
}
