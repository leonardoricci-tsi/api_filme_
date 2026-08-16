import { CommonModule } from '@angular/common';
import {
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnDestroy,
  Output,
  ViewChild,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';

import { CommentsService } from '../../core/services/comments.service';
import { MovieComment } from '../../models/comment.model';

@Component({
  selector: 'app-movie-card',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './movie-card.html',
  styleUrl: './movie-card.css',
})
export class MovieCard implements OnDestroy {
  @Input({ required: true }) tmdbMovieId!: number;
  @Input({ required: true }) titulo!: string;
  @Input() posterUrl: string | null = null;
  @Input() posterPath: string | null = null;
  @Input() sinopse: string | null = null;
  @Input() isFavorito = false;

  @Output() toggleFavorito = new EventEmitter<void>();

  @ViewChild('dialogComentarios') dialogRef?: ElementRef<HTMLDialogElement>;

  // Estado atualizado dentro de callbacks assíncronos (HTTP) precisa ser
  // signal — sem zone.js, mutar um campo comum aqui não dispara re-render.
  comentarios = signal<MovieComment[]>([]);
  carregandoComentarios = signal(false);
  erro = signal('');
  sucesso = signal('');

  // Também é signal: é limpo dentro do callback assíncrono do POST
  // (mesmo motivo dos campos acima).
  novoComentario = signal('');

  private timeoutSucesso?: ReturnType<typeof setTimeout>;

  constructor(private readonly commentsService: CommentsService) {}

  ngOnDestroy(): void {
    clearTimeout(this.timeoutSucesso);
  }

  abrirComentarios(): void {
    this.carregarComentarios();
    this.dialogRef?.nativeElement.showModal();
  }

  fecharComentarios(): void {
    this.dialogRef?.nativeElement.close();
    this.limparSucesso();
  }

  private mostrarSucesso(mensagem: string): void {
    this.limparSucesso();
    this.sucesso.set(mensagem);
    this.timeoutSucesso = setTimeout(() => this.sucesso.set(''), 2500);
  }

  private limparSucesso(): void {
    clearTimeout(this.timeoutSucesso);
    this.sucesso.set('');
  }

  private carregarComentarios(): void {
    this.carregandoComentarios.set(true);
    this.commentsService.listar(this.tmdbMovieId).subscribe({
      next: (comentarios) => {
        this.comentarios.set(comentarios);
        this.carregandoComentarios.set(false);
      },
      error: () => {
        this.erro.set('Não foi possível carregar os comentários.');
        this.carregandoComentarios.set(false);
      },
    });
  }

  enviarComentario(): void {
    const texto = this.novoComentario().trim();
    if (!texto) return;

    this.commentsService
      .criar({
        tmdb_movie_id: this.tmdbMovieId,
        titulo: this.titulo,
        poster_path: this.posterPath,
        texto,
      })
      .subscribe({
        next: (comentario) => {
          this.comentarios.update((atual) => [comentario, ...atual]);
          this.novoComentario.set('');
          this.erro.set('');
          this.mostrarSucesso('Comentário enviado!');
        },
        error: () => {
          this.erro.set('Não foi possível enviar o comentário.');
        },
      });
  }

  removerComentario(id: number): void {
    this.commentsService.remover(id).subscribe({
      next: () => {
        this.comentarios.update((atual) => atual.filter((c) => c.id !== id));
        this.mostrarSucesso('Comentário removido!');
      },
      error: () => {
        this.erro.set('Não foi possível remover o comentário.');
      },
    });
  }
}
