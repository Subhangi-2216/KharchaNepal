import React, { useEffect } from 'react';

const OAuthCallback: React.FC = () => {
  useEffect(() => {
    // Get URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const oauthSuccess = urlParams.get('oauth_success');
    const oauthError = urlParams.get('oauth_error');
    const email = urlParams.get('email');

    // Send message to parent window
    if (window.opener) {
      if (oauthSuccess === 'true') {
        window.opener.postMessage({
          type: 'GMAIL_OAUTH_SUCCESS',
          email: email || 'Unknown'
        }, window.location.origin);
      } else if (oauthError) {
        window.opener.postMessage({
          type: 'GMAIL_OAUTH_ERROR',
          error: oauthError
        }, window.location.origin);
      }
      
      // Close the popup
      window.close();
    } else {
      // Fallback: redirect to settings page if not in popup
      window.location.href = '/settings';
    }
  }, []);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          Processing Gmail Authorization...
        </h2>
        <p className="text-gray-600">
          This window will close automatically.
        </p>
      </div>
    </div>
  );
};

export default OAuthCallback;
