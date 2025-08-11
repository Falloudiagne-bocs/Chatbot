import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MarkdownModule } from 'ngx-markdown';
import { MarkdownComponent } from 'ngx-markdown'; 
import { SocketService } from '../socket.service';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css'],
  standalone: true,
  imports: [CommonModule, FormsModule,  MarkdownComponent], 
  
})
export class ChatComponent {
  question = '';
  messages: { from: 'user' | 'bot', text: string }[] = [];
  loading = false; // Ajoute cette ligne

  constructor(private socketService: SocketService) {}

  ngOnInit() {
    // ✅ Message d'accueil du bot
    this.messages.push({
      from: 'bot',
      text: ` Bienvenue sur Chat-BOCS, Je suis là pour vous aider. Posez-moi une question à tout moment.`
    });

    // 🎧 Réception des réponses du backend
    this.socketService.on('response', (data) => {
      this.loading = false;
      console.log('Réponse reçue du backend :', data);
      this.messages.push({ from: 'bot', text: data.response });
    });
  }

  sendMessage() {
    if (this.question.trim()) {
      this.messages.push({ from: 'user', text: this.question });
      this.loading = true; // Active le loader
      this.socketService.emit('ask', { question: this.question });
      this.question = '';
    }
  }
}
