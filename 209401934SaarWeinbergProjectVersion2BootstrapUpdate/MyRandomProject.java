import java.util.concurrent.Semaphore;

/*
 * This class creates a random number generator based on threads' unpredictable scheduling.
 * Twenty threads are started simultaneously, and the thread whose run method finishes last helps determine the random number.
 */
public class MyRandomProject {

    // Variables to hold random digit values selected by the threads
    private static int random = 0;
    private static int random2 = 0;

    // Counter to track how many threads have finished
    private static int sharedCounter = 0;
    private Thread[] arr0to100;

    // Constructor: Initializes an array of 20 threads, each named by its index
    public MyRandomProject() {
        arr0to100 = new Thread[20];
        for (Integer i = 0; i < 20; i++) {
            Thread t = new Thread(new MyRunnable());
            t.setName(i.toString());
            arr0to100[i] = t;
        }
    }

    // Generates a random integer between 0 and 1,000,000,000 using four "thread randomness" calls
    public Integer getRandom0to1000000000() {
        return getRandom0to100() + getRandom0to100() * 100 + getRandom0to100() * 10000 + getRandom0to100() * 1000000;
    }

    // Generates a random integer between 0 and the specified upper bound using four thread-based numbers (modulo num)
    public Integer getRandom0toNumUntil1000000000(int num) {
        return (getRandom0to100() + getRandom0to100() * 100 + getRandom0to100() * 10000 + getRandom0to100() * 1000000) % num;
    }

    // Generates a random integer with approximately the same number of digits as 'num'
    public Integer getrandomWithNdigits(int num) {
        int to_return = 0;
        int digits = (int) Math.log10(num) + 1; // Determine the number of digits in num

        // Calculate how many two-digit "blocks" to use based on the digit count
        if (digits % 2 == 0)
            digits = digits / 2;
        else {
            digits = (digits / 2) + 1;
        }

        int digits_jumps = 1; // Used for multiplying and shifting the random digits

        for (int i = 0; i < digits; i++) {
            to_return += getRandom0to100() * digits_jumps;
            digits_jumps = digits_jumps * 100;
        }
        // Truncate to the range [0, num)
        to_return = to_return % num;
        return to_return;
    }

    /*
     * Starts all 20 threads simultaneously and waits for them to finish.
     * Each thread will potentially update the shared random values.
     * After all threads finish, resets the array for the next round.
     * Returns a number composed of two random digits from different points in the thread execution.
     */
    public Integer getRandom0to100() {
        for (int i = 0; i < 20; i++) {
            arr0to100[i].start();
        }
        try {
            for (int i = 0; i < 20; i++) {
                arr0to100[i].join(); // Wait for each thread to finish
            }
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }

        String name = "";
        // Reset the threads for future calls, preserving their names
        for (int i = 0; i < 20; i++) {
            name = arr0to100[i].getName();
            arr0to100[i] = new Thread(new MyRunnable());
            arr0to100[i].setName(name);
        }
        sharedCounter = 0; // Reset counter for next use
        return random * 10 + random2;
    }

    /*
     * Inner class used for thread logic. Each thread represents a digit.
     * When all threads finish, the last determines random, and the 11th determines random2.
     * The synchronization assures only one thread updates each variable per specified finish order.
     */
    static class MyRunnable implements Runnable {
        public MyRunnable() {
        }
        @Override
        public void run() {
            /*
             * All 20 threads compete for access to the synchronized block.
             * The order in which threads execute is nondeterministic,
             * which is what gives the process its randomness.
             */
            synchronized (this) {
                int r = Integer.parseInt(String.valueOf(Thread.currentThread().getName()));
                ++sharedCounter;
                // The 20th thread to finish updates "random" (modulo 10 for digits)
                if (sharedCounter == 20) {
                    random = r;
                    if (random > 9)
                        random = random - 10;
                }
                // The 11th thread to finish updates "random2" (modulo 10 for digits)
                if (sharedCounter == 11) {
                    random2 = r;
                    if (random2 > 9)
                        random2 = random2 - 10;
                }
            }
        }
    }

    // Main entry point: parses the input as upper bound, creates generator, and prints a random value in that range
    public static void main(String[] args) {
        if (args.length == 0) {
            System.out.println("MyRandomProject need input for upper bound");
            return;
        }
        int uper_bound = Integer.parseInt(args[0]);
        MyRandomProject b = new MyRandomProject();
        System.out.println(b.getrandomWithNdigits(Math.abs(uper_bound)));
    }
}
