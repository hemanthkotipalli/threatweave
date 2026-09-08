# =============================================================================
# apps/web/Dockerfile — ThreatWeave Web Frontend (Production)
# =============================================================================
# Multi-stage Next.js build for docker-compose local verification.
#
# ROLE OF THIS DOCKERFILE:
# Vercel natively builds and deploys Next.js from a git push without needing
# a Dockerfile — it is the planned production frontend deployment target.
# This Dockerfile exists for:
#   1. Full-stack local verification via docker-compose.prod.yml
#   2. Deployment fallback if Vercel becomes unavailable or the team moves
#      to a self-hosted environment (Render, Fly.io, etc.)
#
# It is NOT used for actual Vercel deployments, which handle their own build.
#
# Stages:
#   deps    — installs production node_modules only
#   builder — runs `next build` with standalone output
#   runtime — minimal node:alpine image copying .next/standalone only
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1 — deps: install production dependencies
# -----------------------------------------------------------------------------
FROM node:20-alpine AS deps

# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine
# for why libc6-compat may be needed
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package manifests first for layer caching
COPY package.json package-lock.json ./

# Install all dependencies needed for building
RUN npm install

# -----------------------------------------------------------------------------
# Stage 2 — builder: run `next build`
# -----------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy node_modules from deps stage (production deps)
COPY --from=deps /app/node_modules ./node_modules

# Copy all source files
COPY . .

# NEXT_PUBLIC_API_URL can be set at build time to bake in the backend URL.
# Defaults to the docker-compose internal service name for local stack runs.
ARG NEXT_PUBLIC_API_URL=http://api:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the application — next.config.ts has output: "standalone" which
# produces a self-contained .next/standalone/ directory at build time.
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 3 — runtime: lean Node image with only the standalone output
# -----------------------------------------------------------------------------
FROM node:20-alpine AS runtime

WORKDIR /app

ENV NODE_ENV=production
# Disable Next.js telemetry in production containers
ENV NEXT_TELEMETRY_DISABLED=1

# The standalone output bundles a minimal server.js and only the required
# node_modules subset — total image is ~200MB vs ~1GB+ with full node_modules.
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs && \
    chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# next start is handled by the standalone server.js
CMD ["node", "server.js"]
