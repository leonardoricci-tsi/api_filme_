import { CommonModule } from '@angular/common';
import { Component, OnInit, signal } from '@angular/core';

import { QuizService } from '../../core/services/quiz.service';
import { QuizResposta, QuizRodada } from '../../models/quiz.model';

@Component({
  selector: 'app-quiz',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './quiz.html',
  styleUrl: './quiz.css',
})
export class Quiz implements OnInit {
  readonly LETRAS = ['a', 'b', 'c', 'd'];

  rodada = signal<QuizRodada | null>(null);
  carregando = signal(true);
  enviando = signal(false);
  respostaEscolhida = signal<string | null>(null);
  resultado = signal<QuizResposta | null>(null);
  erro = signal(false);

  constructor(private readonly quizService: QuizService) {}

  ngOnInit(): void {
    this.novaRodada();
  }

  get imagemSrc(): string | null {
    const rodada = this.rodada();
    return rodada ? `data:image/png;base64,${rodada.imagem_base64}` : null;
  }

  novaRodada(): void {
    this.carregando.set(true);
    this.erro.set(false);
    this.respostaEscolhida.set(null);
    this.resultado.set(null);
    this.quizService.novaRodada().subscribe({
      next: (rodada) => {
        this.rodada.set(rodada);
        this.carregando.set(false);
      },
      error: () => {
        this.erro.set(true);
        this.carregando.set(false);
      },
    });
  }

  escolher(opcao: string): void {
    const rodada = this.rodada();
    if (!rodada || this.enviando() || this.resultado()) {
      return;
    }

    this.respostaEscolhida.set(opcao);
    this.enviando.set(true);
    this.quizService.responder({ round_id: rodada.round_id, resposta: opcao }).subscribe({
      next: (resultado) => {
        this.resultado.set(resultado);
        this.enviando.set(false);
      },
      error: () => {
        this.enviando.set(false);
        this.respostaEscolhida.set(null);
      },
    });
  }
}
