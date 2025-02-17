// Function to handle adding/removing from wishlist
function toggleWishlist(productId) {
    fetch(`/add_to_wishlist/${productId}`)
        .then(response => response.text())
        .then(data => {
            // Find and toggle the specific heart icon for this product
            let wishlistIcon = document.querySelector(`.favorite-btn[onclick*="${productId}"] i`);
            if (wishlistIcon) {
                wishlistIcon.classList.toggle('active');
            }
        })
        .catch(error => console.log('Error:', error));
}

// Function to add to cart
function addToCart(productId, productName, productImage, productPrice) {
    const data = {
        product_id: productId,
        product_name: productName,
        product_image: productImage,
        product_price: productPrice,
        quantity: 1
    };

    fetch('/add_to_cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.text())
    .then(() => {
        const confirmationMessage = document.createElement('div');
        confirmationMessage.className = 'confirmation-message';
        confirmationMessage.innerText = 'Product added to cart!';
        document.body.appendChild(confirmationMessage);

        setTimeout(() => {
            document.body.removeChild(confirmationMessage);
        }, 2000);
    })
    .catch(error => console.error('Error:', error));
}

function updateCartCount() {
    const cartLink = document.querySelector('.nav-icons a[title="Cart"]');
    fetch('/cart/count')
        .then(response => response.json())
        .then(data => {
            if (data.count > 0) {
                cartLink.setAttribute('data-count', data.count);
            } else {
                cartLink.removeAttribute('data-count');
            }
        });
}

function toggleCart(productId, productName, productImage, productPrice, quantity) {
    const cartData = {
        'product_id': productId,
        'product_name': productName,
        'product_image': productImage,
        'product_price': productPrice,
        'quantity': quantity
    };

    fetch('/add_to_cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(cartData)
    })
    .then(response => response.text())
    .then(() => {
        let cartIcon = document.getElementById('cart-icon');
        cartIcon.classList.add('active');
        
        updateCartCount();

        const confirmationMessage = document.createElement('div');
        confirmationMessage.className = 'confirmation-message';
        confirmationMessage.innerText = 'Product added to cart!';
        document.body.appendChild(confirmationMessage);

        setTimeout(() => {
            document.body.removeChild(confirmationMessage);
        }, 2000);
    })
    .catch(error => console.log('Error:', error));
}

document.addEventListener('DOMContentLoaded', updateCartCount);

// Function to update price based on selected product variation
function updatePrice(variationId) {
    const variation = variations.find(v => v.id == variationId);
    if (variation) {
        document.getElementById('product-price').innerText = `$${variation.price}`;
    }
}

// Global variable to store product variations data
const variations = {{ product.variations | tojson }};
