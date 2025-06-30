document.addEventListener('DOMContentLoaded', function () {
            const form = document.querySelector('form');
            form.addEventListener('submit', function (e) {
                const username = form.username.value.trim();
                const email = form.email.value.trim();
                const password = form.password.value;

                let valid = true;
                
                let emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

                if (username.length < 3) {
                    alert('Username must be at least 3 characters.');
                    valid = false;
                } else if (/\d/.test(username)) {
                    alert('Username must not contain numbers.');
                    valid = false;
                } else if (!emailPattern.test(email)) {
                    alert('Please enter a valid email address.');
                    valid = false;
                } else if (password.length < 6) {
                    alert('Password must be at least 6 characters.');
                    valid = false;
                }

                if (!valid) {
                    e.preventDefault();
                }
            });
        });