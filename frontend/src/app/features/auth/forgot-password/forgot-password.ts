import { CommonModule } from '@angular/common';
import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './forgot-password.html',
  styleUrl: '../auth-shared.css',
})
export class ForgotPassword {
  email = '';
  mensagem = signal('');
  erro = signal('');
  carregando = signal(false);

  constructor(private readonly authService: AuthService) {}

  enviar(): void {
    this.erro.set('');
    this.mensagem.set('');
    this.carregando.set(true);

    this.authService.forgotPassword({ email: this.email }).subscribe({
      next: (resposta) => {
        this.carregando.set(false);
        this.mensagem.set(resposta.detail);
      },
      error: (erro) => {
        this.carregando.set(false);
        this.erro.set(erro?.error?.detail ?? 'Não foi possível processar o pedido.');
      },
    });
  }
}
