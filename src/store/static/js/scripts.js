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
