document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({
        behavior: 'smooth'
      });
    }
  });
});

document.addEventListener("DOMContentLoaded", () => {
  // ===============================
  // Loading screen timeout fallback
  // ===============================
  const loadingScreen = document.getElementById("loading");
  const featuredProducts = document.getElementById("featured-products");

  if (loadingScreen && featuredProducts) {
    loadingScreen.style.display = "none";
    featuredProducts.style.display = "block";
  }

  setTimeout(() => {
    if (loadingScreen && loadingScreen.style.display !== "none") {
      loadingScreen.style.display = "none";
      const timeoutMessage = document.createElement("div");
      timeoutMessage.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255, 255, 255, 0.9); display: flex; justify-content: center; align-items: center; z-index: 9999;">
          <div style="text-align: center;">
            <p class="mt-3" style="font-size: 1.25rem; color: #6c757d; font-weight: 500;">
              The page is taking too long to load. Please try again later.
            </p>
          </div>
        </div>`;
      document.body.appendChild(timeoutMessage);
    }
  }, 10000);

  // ========================
  // Category Toggle Function
  // ========================
  const toggleBtn = document.getElementById("toggle-category");
  const extraItems = document.querySelectorAll(".extra-cat");
  let expanded = false;

  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      expanded = !expanded;
      extraItems.forEach((el) => el.classList.toggle("d-none"));
      toggleBtn.innerHTML = expanded
        ? '<span>See Less</span> <i class="fas fa-chevron-up small"></i>'
        : '<span>See More</span> <i class="fas fa-chevron-down small"></i>';
    });
  }

  // =====================
  // Add to Cart via AJAX
  // =====================
  document.querySelectorAll(".add-to-cart-form").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      const url = form.action;

      try {
        const res = await fetch(url, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": formData.get("csrfmiddlewaretoken"),
          },
          body: formData,
        });

        if (res.ok) {
          const data = await res.json();
          const badge = document.getElementById("cart-badge");
          if (badge) {
            badge.textContent = data.cart_total;
            badge.style.display = data.cart_total > 0 ? "inline-block" : "none";
          }

          form.outerHTML = `
            <button class="btn btn-outline-secondary w-100" disabled>
              <i class="fas fa-check me-2"></i>Already in Cart
            </button>`;
        } else {
          console.error("Failed to add to cart");
        }
      } catch (err) {
        console.error("Error adding to cart:", err);
      }
    });
  });

  // ====================
  // Copy Promo Code
  // ====================
  const copyBtn = document.querySelector(".copy-btn");
  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      navigator.clipboard.writeText("SALE20").then(() => {
        alert("Promo code copied to clipboard!");
      });
    });
  }

  // ========================================
  // Quantity + / - Handling with Debounce
  // ========================================
  function debounce(fn, delay) {
    let timeout;
    return function (...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  document.querySelectorAll(".auto-submit-qty").forEach(function (input) {
    const debouncedSubmit = debounce(function () {
      input.closest("form").submit();
    }, 500);

    // Listen for input changes (typing)
    input.addEventListener("input", debouncedSubmit);

    const wrapper = input.closest(".quantity-wrapper");
    if (wrapper) {
      wrapper.querySelectorAll(".quantity-btn").forEach(function (btn) {
        btn.addEventListener("click", function () {
          let value = parseInt(input.value, 10) || 1;

          if (btn.classList.contains("plus-btn")) {
            value++;
          } else if (btn.classList.contains("minus-btn") && value > 1) {
            value--;
          }

          input.value = value;
          input.dispatchEvent(new Event("input", { bubbles: true })); // ensure event propagates
        });
      });
    }
  });

  // ======================
  // Delete Cart Item AJAX
  // ======================
  document.querySelectorAll(".delete-cart-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      const form = btn.closest("form");
      const action = form.action;
      const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;

      fetch(action, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
        },
      })
        .then((res) => {
          if (!res.ok) throw new Error("Failed to delete");
          form.closest(".row").remove();
        })
        .catch((err) => console.error(err));
    });
  });

  // ==========================
  // Payment Method Highlight
  // ==========================
  document.querySelectorAll(".form-check").forEach(function (check) {
    check.addEventListener("click", function () {
      const radio = this.querySelector('input[type="radio"]');
      radio.checked = true;

      document.querySelectorAll(".form-check").forEach(function (el) {
        el.classList.remove("bg-light");
      });
      this.classList.add("bg-light");
    });
  });
});

// ===============================
// Live Quantity Update for Subtotal
// ===============================
document.querySelectorAll(".quantity-input").forEach((input) => {
  const debounce = (fn, delay) => {
    let timeout;
    return (...args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => fn(...args), delay);
    };
  };

  const updateSubtotal = debounce(async (input) => {
    const form = input.closest("form");
    const url = form.action;
    const formData = new FormData(form);

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": formData.get("csrfmiddlewaretoken"),
        },
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        const subtotalElement = form.closest(".row").querySelector(".price-tag");
        if (subtotalElement) {
          subtotalElement.textContent = `₱${data.subtotal.toFixed(2)}`;
        }
      } else {
        console.error("Failed to update subtotal");
      }
    } catch (err) {
      console.error("Error updating subtotal:", err);
    }
  }, 500);

  input.addEventListener("input", () => updateSubtotal(input));
});

// product advertisement section
function startCountdowns() {
  const countdownElements = document.querySelectorAll('.countdown');

  countdownElements.forEach((countdown) => {
    const timerContainer = countdown.querySelector('.countdown-timer');
    const endTime = new Date(countdown.dataset.endtime).getTime();

    function updateTimer() {
      const now = new Date().getTime();
      const distance = endTime - now;

      if (distance < 0) {
        timerContainer.innerHTML = '<div class="time-block"><span class="time">0</span><span class="label">EXPIRED</span></div>';
        return;
      }

      const days = Math.floor(distance / (1000 * 60 * 60 * 24));
      const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((distance % (1000 * 60)) / 1000);

      timerContainer.innerHTML = `
        ${days > 0 ? `<div class="time-block"><span class="time">${days}</span><span class="label">DAYS</span></div>` : ''}
        <div class="time-block"><span class="time">${String(hours).padStart(2, '0')}</span><span class="label">HRS</span></div>
        <div class="time-block"><span class="time">${String(minutes).padStart(2, '0')}</span><span class="label">MIN</span></div>
        <div class="time-block"><span class="time">${String(seconds).padStart(2, '0')}</span><span class="label">SEC</span></div>
      `;
    }

    updateTimer();
    setInterval(updateTimer, 1000);
  });
}

document.addEventListener("DOMContentLoaded", startCountdowns);

// 

// products.html

// dre ibutang