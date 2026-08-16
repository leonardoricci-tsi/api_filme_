import { CommonModule } from '@angular/common';
import { Component, OnInit, signal } from '@angular/core';

import { CommentsService } from '../../core/services/comments.service';
import { MovieComment } from '../../models/comment.model';

@Component({
  selector: 'app-comments',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './comments.html',
  styleUrl: './comments.css',
})
export class Comments implements OnInit {
  comentarios = signal<MovieComment[]>([]);
  carregando = signal(true);

  constructor(private readonly commentsService: CommentsService) {}

  ngOnInit(): void {
    this.carregarComentarios();
  }

  private carregarComentarios(): void {
    this.carregando.set(true);
    this.commentsService.listar().subscribe({
      next: (comentarios) => {
        this.comentarios.set(comentarios);
        this.carregando.set(false);
      },
      error: () => this.carregando.set(false),
    });
  }

  posterUrl(posterPath: string | null): string | null {
    return posterPath ? `https://image.tmdb.org/t/p/w500${posterPath}` : null;
  }

  remover(comentario: MovieComment): void {
    // Atualização otimista: some da lista na hora, sem esperar um novo GET.
    this.comentarios.update((atual) => atual.filter((c) => c.id !== comentario.id));
    this.commentsService.remover(comentario.id).subscribe({
      error: () => this.carregarComentarios(), // reverte pro estado real se falhar
    });
  }
}
