
        var config = {
            mode: "fixed_servers",
            rules: {
            singleProxy: {
                scheme: "http",
                host: "brd.superproxy.io",
                port: parseInt(33335)
            },
            bypassList: ["localhost"]
            }
        };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                username: "brd-customer-hl_4558780a-zone-chiri_scraper",
                password: "7cw1nvv2hwkc"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
        );
        