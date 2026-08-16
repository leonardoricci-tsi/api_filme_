import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { CommentPayload, MovieComment } from '../../models/comment.model';

@Injectable({ providedIn: 'root' })
export class CommentsService {
  constructor(private readonly http: HttpClient) {}

  listar(tmdbMovieId?: number): Observable<MovieComment[]> {
    const params = tmdbMovieId ? new HttpParams().set('tmdb_movie_id', tmdbMovieId) : undefined;
    return this.http.get<MovieComment[]>('/comments', { params });
  }

  criar(payload: CommentPayload): Observable<MovieComment> {
    return this.http.post<MovieComment>('/comments', payload);
  }

  remover(id: number): Observable<void> {
    return this.http.delete<void>(`/comments/${id}`);
  }
}
