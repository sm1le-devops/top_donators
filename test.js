async function getSomething() {
    return new Promise((fullfill) => {
        setTimeout(() => {
            fullfill("VLADD")
        },3000  )
    })
}
getSomething().then((something) => {
    console.log(something)
})