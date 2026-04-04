.PHONY: dev caddy shell logs 404 migrate makemigrations deploy-static

dev:
	echo localhost:1414
	python manage.py runserver 0:1414

caddy:
	caddy run --config Caddyfile.dev

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

shell:
	heroku run python manage.py shell --app bear-blog

logs:
	heroku logs --tail --app bear-blog --force-colors | grep "app\[web" | grep -Ev "(GET|POST|HEAD|OPTIONS)"

404:
	heroku logs --tail --app bear-blog --force-colors | grep "heroku\[" | grep "404"

router:
	heroku logs --tail --app bear-blog --force-colors | grep "heroku\[router" | grep -Ev "feed"

deploy-static:
	@echo "🚀 Deploying static files for production..."
	@./deploy_markdownx_static.sh
	@./deploy_debug_toolbar_static.sh
	@python manage.py collectstatic --noinput
	@echo "✅ Static files deployment complete!"