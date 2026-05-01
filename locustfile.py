from locust import HttpUser, task, between

class SnapLinkUser(HttpUser):
    wait_time = between(1, 2)

    @task(1)
    def shorten_url(self):
        with self.client.post(
            "/shorten",
            json={"url": "https://github.com"},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()

    @task(3)
    def redirect(self):
        with self.client.get(
            "/XDslBp",
            allow_redirects=False,
            catch_response=True
        ) as response:
            if response.status_code == 307:
                response.success()