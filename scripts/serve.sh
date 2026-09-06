#!/bin/sh
# Build or serve the site locally with the same Ruby GitHub Pages uses.
# Usage: scripts/serve.sh          -> bundle install (if needed) + jekyll serve
#        scripts/serve.sh build    -> bundle install (if needed) + jekyll build
set -e
cd "$(dirname "$0")/.."

RUBY_BIN="$(brew --prefix ruby@3.3 2>/dev/null)/bin"
if [ ! -x "$RUBY_BIN/ruby" ]; then
  echo "Ruby 3.3 not found. Install it with: brew install ruby@3.3" >&2
  exit 1
fi
export PATH="$RUBY_BIN:$PATH"
export PATH="$(gem environment gemdir)/bin:$PATH"
# The github-pages gem's SCSS is UTF-8; a C/POSIX locale makes it fail to compile.
export LANG="${LANG:-en_US.UTF-8}"
export LC_ALL="${LC_ALL:-en_US.UTF-8}"

command -v bundle >/dev/null 2>&1 || gem install bundler --no-document
bundle config set --local path vendor/bundle >/dev/null
bundle check >/dev/null 2>&1 || bundle install

if [ "${1:-serve}" = "build" ]; then
  exec bundle exec jekyll build
else
  exec bundle exec jekyll serve --port 4000
fi
