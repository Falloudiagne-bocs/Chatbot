import { Component } from '@angular/core';
import { ChatComponent } from './chat/chat.component';

@Component({
  standalone: true,
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  imports: [ChatComponent],
})
export class AppComponent {}
