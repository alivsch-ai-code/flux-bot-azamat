import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    // Keep logging minimal but visible in debug console.
    // eslint-disable-next-line no-console
    console.error('WebApp fatal render error:', error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 16, color: '#fff' }}>
          <h3>⚠️ App-Fehler</h3>
          <p>Die Ansicht konnte nicht geladen werden. Bitte Mini App neu öffnen.</p>
        </div>
      );
    }
    return this.props.children;
  }
}
