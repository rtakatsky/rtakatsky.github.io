# Local preview only. GitHub Pages builds the site itself with the same gem.
source "https://rubygems.org"

# GitHub Pages builds with Ruby 3.3. Ruby 4 makes Bundler pick an ancient
# github-pages release, so refuse it up front. Use scripts/serve.sh.
ruby ">= 3.2", "< 4"
gem "github-pages", group: :jekyll_plugins
gem "webrick"
# Standard-library gems that newer Rubies no longer bundle by default.
gem "csv"
gem "base64"
gem "bigdecimal"
gem "logger"
