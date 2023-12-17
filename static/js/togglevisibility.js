function toggleVisibility(productId, productStatus) {
    let newStatus = '';

    // Determine the new status based on the current status
    if (productStatus === 'activated') {
        newStatus = 'deactivated';
    } else if (productStatus === 'deactivated') {
        newStatus = 'activated';
    } else if (productStatus === 'disabled') {
        newStatus = 'activated';
    }

    // Make an AJAX POST request to update the product status
    $.ajax({
        type: 'POST',
        url: '/update_product_status',
        data: {
            product_id: productId,
            status: newStatus
        },
        success: function(response) {
            // Update product visibility in the index page upon success
            if (response === 'success') {
                let productElement = document.getElementById(productId);
                productElement.style.display = (newStatus === 'activated' || newStatus === 'disabled') ? 'none' : 'block';
            }
        },
        error: function(error) {
            console.log('Error:', error);
        }
    });
}