from signals import Data, Computed, Effect, Time


time = Time()
name = Data("Andris")

@Computed
def greeting():
    return f"Hey {name.value}! its {time.value}"

@Effect
def print_result():
    print(greeting.value)

async def main():
    print_result()
    await time.start()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())  # Run the event loop