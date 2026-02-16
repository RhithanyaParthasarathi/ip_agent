import React from 'react';
import { Bot } from 'lucide-react';
import './Header.css';

function Header() {
  return (
    <header className="header">
      <div className="header-content">
        <div className="bot-icon">
          <Bot size={32} />
        </div>
      </div>
    </header>
  );
}

export default Header;
