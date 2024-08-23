// Here are some relevant code fragments from other files of the repo:
// --------------------------------------------------
// the below code fragment can be found in:
// commons-collections/src/main/java/org/apache/commons/collections4/IterableUtils.java
// --------------------------------------------------
//      * <p>
//      * A <code>null</code> or empty iterable returns false.
//      *
//      * @param <E> the type of object the {@link Iterable} contains
//      * @param iterable  the iterable to check, may be null
//      * @param object  the object to check
//      * @return true if the object is contained in the iterable, false otherwise
//      */
//     public static <E> boolean contains(final Iterable<E> iterable, final Object object) {
//         if (iterable instanceof Collection<?>) {
//             return ((Collection<E>) iterable).contains(object);
//         } else {
//             return IteratorUtils.contains(emptyIteratorIfNull(iterable), object);
//         }
//     }
// 
//     /**
//      * Checks if the object is contained in the given iterable. Object equality
//      * is tested with an {@code equator} unlike {@link #contains(Iterable, Object)}
//      * which uses {@link Object#equals(Object)}.
// --------------------------------------------------
// the below code fragment can be found in:
// commons-collections/src/main/java/org/apache/commons/collections4/MapUtils.java
// --------------------------------------------------
//      *
//      * @param map  the map to check, may be null
//      * @return true if non-null and non-empty
//      * @since 3.2
//      */
//     public static boolean isNotEmpty(final Map<?,?> map) {
//         return !MapUtils.isEmpty(map);
//     }
// 
//     // Map decorators
//     //-----------------------------------------------------------------------
//     /**
//      * Returns a synchronized map backed by the given map.
//      * <p>
//      * You must manually synchronize on the returned buffer's iterator to
//      * avoid non-deterministic behavior:
//      *
//      * <pre>
//      * Map m = MapUtils.synchronizedMap(myMap);
//      * Set s = m.keySet();  // outside synchronized block
// --------------------------------------------------
// the below code fragment can be found in:
// commons-collections/src/main/java/org/apache/commons/collections4/IteratorUtils.java
// --------------------------------------------------
//      */
//     public static <E> ResettableListIterator<E> arrayListIterator(final Object array) {
//         return new ArrayListIterator<E>(array);
//     }
// 
//     /**
//      * Gets a list iterator over the end part of an object array.
//      *
//      * @param <E> the element type
//      * @param array  the array over which to iterate
//      * @param start  the index to start iterating at
//      * @return a list iterator over part of the array
//      * @throws IndexOutOfBoundsException if start is less than zero
//      * @throws NullPointerException if array is null
//      */
//     public static <E> ResettableListIterator<E> arrayListIterator(final E[] array, final int start) {
//         return new ObjectArrayListIterator<E>(array, start);
//     }
// 
//     /**
// --------------------------------------------------
// the below code fragment can be found in:
// commons-collections/src/main/java/org/apache/commons/collections4/IteratorUtils.java
// --------------------------------------------------
//      *
//      * @param obj  the object to convert to an iterator
//      * @return a suitable iterator, never null
//      */
//     public static Iterator<?> getIterator(final Object obj) {
//         if (obj == null) {
//             return emptyIterator();
//         }
//         if (obj instanceof Iterator) {
//             return (Iterator<?>) obj;
//         }
//         if (obj instanceof Iterable) {
//             return ((Iterable<?>) obj).iterator();
//         }
//         if (obj instanceof Object[]) {
//             return new ObjectArrayIterator<Object>((Object[]) obj);
//         }
//         if (obj instanceof Enumeration) {
//             return new EnumerationIterator<Object>((Enumeration<?>) obj);
//         }
// --------------------------------------------------
// the below code fragment can be found in:
// commons-collections/src/main/java/org/apache/commons/collections4/IteratorUtils.java
// --------------------------------------------------
//      * Gets a list iterator over an object or primitive array.
//      * <p>
//      * This method will handle primitive arrays as well as object arrays.
//      * The primitives will be wrapped in the appropriate wrapper class.
//      *
//      * @param <E> the element type
//      * @param array  the array over which to iterate
//      * @return a list iterator over the array
//      * @throws IllegalArgumentException if the array is not an array
//      * @throws NullPointerException if array is null
//      */
//     public static <E> ResettableListIterator<E> arrayListIterator(final Object array) {
//         return new ArrayListIterator<E>(array);
//     }
// 
//     /**
//      * Gets a list iterator over the end part of an object array.
//      *
//      * @param <E> the element type
//      * @param array  the array over which to iterate
// --------------------------------------------------
// the below code fragment can be found in:
// commons-collections/src/main/java/org/apache/commons/collections4/IteratorUtils.java
// --------------------------------------------------
// 
//     /**
//      * Answers true if a predicate is true for every element of an iterator.
//      * <p>
//      * A <code>null</code> or empty iterator returns true.
//      *
//      * @param <E> the type of object the {@link Iterator} contains
//      * @param iterator  the {@link Iterator} to use, may be null
//      * @param predicate  the predicate to use, may not be null
//      * @return true if every element of the collection matches the predicate or if the
//      *   collection is empty, false otherwise
//      * @throws NullPointerException if predicate is null
//      * @since 4.1
//      */
//     public static <E> boolean matchesAll(final Iterator<E> iterator, final Predicate<? super E> predicate) {
//         if (predicate == null) {
//             throw new NullPointerException("Predicate must not be null");
//         }
// 
//         if (iterator != null) {
// --------------------------------------------------
// the below code fragment can be found in:
// commons-collections/src/main/java/org/apache/commons/collections4/IteratorUtils.java
// --------------------------------------------------
//      * @param <E> the type of object the {@link Iterator} contains
//      * @param iterator  the {@link Iterator} to use, may be null
//      * @param predicate  the predicate to use, may not be null
//      * @return true if any element of the collection matches the predicate, false otherwise
//      * @throws NullPointerException if predicate is null
//      * @since 4.1
//      */
//     public static <E> boolean matchesAny(final Iterator<E> iterator, final Predicate<? super E> predicate) {
//         return indexOf(iterator, predicate) != -1;
//     }
// 
//     /**
//      * Answers true if a predicate is true for every element of an iterator.
//      * <p>
//      * A <code>null</code> or empty iterator returns true.
//      *
//      * @param <E> the type of object the {@link Iterator} contains
//      * @param iterator  the {@link Iterator} to use, may be null
//      * @param predicate  the predicate to use, may not be null
//      * @return true if every element of the collection matches the predicate or if the
// --------------------------------------------------
// the below code fragment can be found in:
// commons-collections/src/main/java/org/apache/commons/collections4/IteratorUtils.java
// --------------------------------------------------
//      * @throws IllegalArgumentException if the array is not an array
//      * @throws NullPointerException if array is null
//      */
//     public static <E> ResettableIterator<E> arrayIterator(final Object array) {
//         return new ArrayIterator<E>(array);
//     }
// 
//     /**
//      * Gets an iterator over the end part of an object array.
//      *
//      * @param <E> the element type
//      * @param array  the array over which to iterate
//      * @param start  the index to start iterating at
//      * @return an iterator over part of the array
//      * @throws IndexOutOfBoundsException if start is less than zero or greater
//      *   than the length of the array
//      * @throws NullPointerException if array is null
//      */
//     public static <E> ResettableIterator<E> arrayIterator(final E[] array, final int start) {
//         return new ObjectArrayIterator<E>(array, start);
// --------------------------------------------------
// the below code fragment can be found in:
// commons-collections/src/main/java/org/apache/commons/collections4/IteratorUtils.java
// --------------------------------------------------
//         return iterator == null || !iterator.hasNext();
//     }
// 
//     /**
//      * Checks if the object is contained in the given iterator.
//      * <p>
//      * A <code>null</code> or empty iterator returns false.
//      *
//      * @param <E> the type of object the {@link Iterator} contains
//      * @param iterator  the iterator to check, may be null
//      * @param object  the object to check
//      * @return true if the object is contained in the iterator, false otherwise
//      * @since 4.1
//      */
//     public static <E> boolean contains(final Iterator<E> iterator, final Object object) {
//         return matchesAny(iterator, EqualPredicate.equalPredicate(object));
//     }
// 
//     /**
//      * Returns the <code>index</code>-th value in {@link Iterator}, throwing
// --------------------------------------------------
// the below code fragment can be found in:
// commons-collections/src/main/java/org/apache/commons/collections4/MapUtils.java
// --------------------------------------------------
//      * @since 3.2
//      */
//     public static boolean isEmpty(final Map<?,?> map) {
//         return map == null || map.isEmpty();
//     }
// 
//     /**
//      * Null-safe check if the specified map is not empty.
//      * <p>
//      * Null returns false.
//      *
//      * @param map  the map to check, may be null
//      * @return true if non-null and non-empty
//      * @since 3.2
//      */
//     public static boolean isNotEmpty(final Map<?,?> map) {
//         return !MapUtils.isEmpty(map);
//     }
// 
//     // Map decorators
// --------------------------------------------------

class CollectionUtils {

    /**
     * Returns the <code>index</code>-th <code>Map.Entry</code> in the <code>map</code>'s <code>entrySet</code>,
     * throwing <code>IndexOutOfBoundsException</code> if there is no such element.
     *
     * @param <K>  the key type in the {@link Map}
     * @param <V>  the key type in the {@link Map}
     * @param map  the object to get a value from
     * @param index  the index to get
     * @return the object at the specified index
     * @throws IndexOutOfBoundsException if the index is invalid
     */
    public static <K,V> Map.Entry<K, V> get(final Map<K,V> map, final int index) {
        checkIndexBounds(index);
        return get(map.entrySet(), index);
    }

    /**
     * Gets the size of the collection/iterator specified.
     * <p>
     * This method can handles objects as follows
     * <ul>
     * <li>Collection - the collection size
     * <li>Map - the map size
     * <li>Array - the array size
     * <li>Iterator - the number of elements remaining in the iterator
     * <li>Enumeration - the number of elements remaining in the enumeration
     * </ul>
     *
     * @param object  the object to get the size of, may be null
     * @return the size of the specified collection or 0 if the object was null
     * @throws IllegalArgumentException thrown if object is not recognized
     * @since 3.1
     */
    public static int size(final Object object) {
        if (object == null) {
            return 0;
        }
        int total = 0;
        if (object instanceof Map<?,?>) {
            total = ((Map<?, ?>) object).size();
        } else if (object instanceof Collection<?>) {
            total = ((Collection<?>) object).size();
        } else if (object instanceof Iterable<?>) {
            total = IterableUtils.size((Iterable<?>) object);
        } else if (object instanceof Object[]) {
            total = ((Object[]) object).length;
        } else if (object instanceof Iterator<?>) {
            total = IteratorUtils.size((Iterator<?>) object);
        } else if (object instanceof Enumeration<?>) {
            final Enumeration<?> it = (Enumeration<?>) object;
            while (it.hasMoreElements()) {
                total++;
                it.nextElement();
            }
        } else {
            try {
                total = Array.getLength(object);
            } catch (final IllegalArgumentException ex) {
                throw new IllegalArgumentException("Unsupported object type: " + object.getClass().getName());
            }
        }
        return total;
    }

    /**
     * Checks if the specified collection/array/iterator is empty.
     * <p>
     * This method can handles objects as follows
     * <ul>
     * <li>Collection - via collection isEmpty
     * <li>Map - via map isEmpty
     * <li>Array - using array size
     * <li>Iterator - via hasNext
     * <li>Enumeration - via hasMoreElements
     * </ul>
     * <p>
     * Note: This method is named to avoid clashing with
     * {@link #isEmpty(Collection)}.
     *
     * @param object  the object to get the size of, may be null
     * @return true if empty or null
     * @throws IllegalArgumentException thrown if object is not recognized
     * @since 3.2
     */
    public static boolean sizeIsEmpty(final Object object) {
        //         if (object == null) {
        //     return true;
        // }
        // if (object instanceof Map<?,?>) {
        //     return ((Map<?, ?>) object).isEmpty();
        // } else if (object instanceof Collection<?>) {
        //     return ((Collection<?>) object).isEmpty();
        // } else if (object instanceof Iterable<?>) {
        //     return IterableUtils.isEmpty((Iterable<?>) object);
        // } else if (object instanceof Object[]) {
        //     return ((Object[]) object).length == 0;
        // } else if (object instanceof Iterator<?>) {
        //     return !((Iterator<?>) object).hasNext();
        // } else if (object instanceof Enumeration<?>) {
        //     return !((Enumeration<?>) object).hasMoreElements();
        // } else {
        //     try {
        //         return Array.getLength(object) == 0;
        //     } catch (final IllegalArgumentException ex) {
        //         throw new IllegalArgumentException("Unsupported object type: " + object.getClass().getName());
        //     }
        // }
    
    //
        if (object == null) {
            return true;
        } else if (object instanceof Collection<?>) {
            return ((Collection<?>) object).isEmpty();
        } else if (object instanceof Iterable<?>) {
            return IterableUtils.isEmpty((Iterable<?>) object);
        } else if (object instanceof Map<?, ?>) {
            return ((Map<?, ?>) object).isEmpty();
        } else if (object instanceof Object[]) {
            return ((Object[]) object).length == 0;
        } else if (object instanceof Iterator<?>) {
            return ((Iterator<?>) object).hasNext() == false;
        } else if (object instanceof Enumeration<?>) {
            return ((Enumeration<?>) object).hasMoreElements() == false;
        } else {
            try {
                return Array.getLength(object) == 0;
            } catch (final IllegalArgumentException ex) {
                throw new IllegalArgumentException("Unsupported object type: " + object.getClass().getName());
            }
        }