export class Product {
    constructor(
        public id: number = 0,
        public name: string = "",
        public type: string = "",
        public description: string = "",
        public lastUpdate: Date | undefined = undefined,
        public status: number = 0
    ) {}
}
