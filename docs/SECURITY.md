# NoorAI Security Overview

This document summarises the security measures implemented in the NoorAI
backend, and tracks what remains for production deployment.

## Implemented

### Authentication and Sessions
- [x] Passwords hashed with bcrypt via passlib
- [x] JWT authentication using 30 minute access tokens with HS256
- [x] Refresh token rotation with Redis backed revocation
- [x] Optional auth dependency (optional_current_user) for future
      public or anonymous routes. Returns None for missing tokens and
      raises 401 only for invalid ones
- [x] Soft delete. Deactivated users (is_active false) are rejected at
      token validation

### Network and Transport
- [x] Rate limiting via slowapi:
  - POST /auth/login: 5 requests per minute per IP
  - POST /auth/register: 3 requests per minute per IP
  - POST /auth/refresh: 10 requests per minute per IP
  - All other routes: 60 requests per minute per IP (default)
- [x] CORS restricted to known frontend origins, switched via APP_ENV
      (localhost origins in development, FRONTEND_URL in production)
- [x] Security headers on all responses, including
      X-Content-Type-Options, X-Frame-Options, X-XSS-Protection,
      Content-Security-Policy, and Strict-Transport-Security
      (production only)

### Input Validation
- [x] Pydantic v2 schemas with custom validators throughout
- [x] Registration requires a password of at least 8 characters and
      normalises email addresses to lowercase with whitespace stripped,
      preventing duplicate accounts that differ only by case or
      formatting
- [x] Zakat inputs must be non negative, with a sanity ceiling to
      reject malformed or absurd values
- [x] location_country is validated as a 2 letter ISO 3166-1 alpha-2
      code when provided
- [x] madhab is validated against the five recognised schools
      (hanafi, shafi, maliki, hanbali, jafari)
- [x] calculation_method is derived automatically from
      location_country at registration using a verified lookup table,
      validated against Aladhan's full supported method range at
      import time, and is not editable via PATCH /users/me
- [x] SQL injection is prevented by construction. All queries use
      SQLAlchemy's ORM and parameterised query builder, with no raw
      string concatenated SQL anywhere in the codebase

### Monitoring and Error Handling
- [x] Error monitoring via Sentry, active in production only, with
      send_default_pii set to false
- [x] Global exception handler. Unhandled errors return a generic 500
      response to clients in production with no stack traces or
      internal details leaked, while the full exception is reported to
      Sentry. In development, exceptions surface normally for debugging

### Secrets
- [x] All secrets and environment dependent configuration are loaded
      via pydantic settings from a gitignored .env file, with
      .env.example committed as a placeholder template
- [x] SECRET_KEY rotation behaviour is documented in app/core/config.py.
      Rotating it invalidates all active access and refresh tokens at
      once

## Pending for Production

- [ ] HTTPS enforced at the deployment layer (Railway and Nginx)
- [ ] Attribution link for ExchangeRate API ("Rates by ExchangeRate-API")
      required in the frontend footer by its terms of use
- [ ] Content Security Policy refinement once the frontend's actual
      resource origins (fonts, API host, and so on) are known
- [ ] Dependency vulnerability scanning
- [ ] Security audit by a qualified third party
- [ ] Location based smart defaults for calculation_method currently
      cover a starter set of countries via
      CALCULATION_METHOD_BY_COUNTRY, with a Muslim World League
      fallback for all others. The table can be extended as needed
- [ ] QF_CLIENT_ID and QF_CLIENT_SECRET are present in .env.example but
      not yet wired into Settings or used. These are reserved for future
      Quran Foundation API integration
