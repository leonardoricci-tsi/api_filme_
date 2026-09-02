import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { QuizRespostaPayload, QuizResposta, QuizRodada } from '../../models/quiz.model';

@Injectable({ providedIn: 'root' })
export class QuizService {
  constructor(private readonly http: HttpClient) {}

  novaRodada(): Observable<QuizRodada> {
    return this.http.get<QuizRodada>('/quiz/pixelado');
  }

  responder(payload: QuizRespostaPayload): Observable<QuizResposta> {
    return this.http.post<QuizResposta>('/quiz/pixelado/resposta', payload);
  }
}
