const Pics = Array.from(document.getElementsByClassName('Anh'));
const modal = document.getElementById('modal-plain');
const modalImg = document.getElementById('modal-img');
const closeButton = document.getElementById('close-button');

Pics.forEach(pic => {
    pic.onclick = (e) => {
        modal.style.display = 'block';
        modalImg.src = e.target.src;
    };
});

closeButton.onclick = () => {
    modal.style.display = 'none';
}

modal.onclick = (e) => {
    if (e.target === modalImg) {
        return;
    }
    modal.style.display = 'none';
}   