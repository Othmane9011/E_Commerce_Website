// Function to add a product to the cart
function addToCart(productId, quantity) {
    fetch(`/add_to_cart/${productId}/${quantity}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        // Display a message indicating whether the product was added successfully
        console.log(data.message); // You can replace this with any UI feedback you prefer
    })
    .catch(error => {
        console.error('Error:', error);
    });


}

