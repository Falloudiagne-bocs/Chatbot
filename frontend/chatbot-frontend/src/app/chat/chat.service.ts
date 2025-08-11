import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

interface AskResponse {
  response: string;
}

@Injectable({
  providedIn: 'root',
})
export class ChatService {
  private apiUrl = 'http://localhost:8000/ask';

  constructor(private http: HttpClient) {}

  askQuestion(question: string): Observable<AskResponse> {
    return this.http.post<AskResponse>(this.apiUrl, { question });
  }
}
